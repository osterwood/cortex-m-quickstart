import os
import logging

import pystache
import yaml
import json
import colorlog

from invoke import task

handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(levelname)s %(message)s')
)

logger = colorlog.getLogger('')
logger.setLevel(logging.INFO)
logger.addHandler(handler)

ENV_FILE     = ".env.tasks"
DEVICES_FILE = 'devices.yml'

def merge(x, y):
    z = x.copy()
    z.update(y)
    return z

def env_read():
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE) as json_file:
            data = json.load(json_file)
        return data
    else:
        return {}

def env_save(data):
    with open(ENV_FILE, 'w') as json_file:
        json.dump(data, json_file)

@task(help={'mcu': "Processor to re-target for"})
def target(c, mcu):
    """Setup cargo to build for a particular MCU"""

    if 'mcu' in env_read().keys():
        if env_read()['mcu'] == mcu:
            logging.info("Target already set to {}".format(mcu))
            return

    data = yaml.load(open(DEVICES_FILE, 'r'))
    meta = {'mcu': mcu}

    if mcu not in data.keys():
        keys = ", ".join(sorted(data.keys()))
        logging.error("MCU '{}' is not recognized. Select from: [{}]".format(mcu, keys))
        return

    logging.info("Changing target to {}".format(mcu))
    env_save(dict(mcu=mcu))

    with open('memory.x.mustache') as input_file:
        output = pystache.render(input_file.read(), merge(data[mcu], meta))

        with open('memory.x', 'w') as output_file:
            output_file.write(output)

    config = []
    mode   = "prebuild"
    with open('.cargo/config') as input_file:
        for line in input_file.readlines():

            # Replace the first line with the proper target
            # Doesn't really need to be done as we'll be executing
            # QEMU directly via invoke tasks.
            if line.startswith("[target.thumb"):
                line = "[target.{}]".format(data[mcu]['target'])

            if mode == "inbuild":
                if "\"{}\"".format(data[mcu]['target']) in line:
                    # Make sure the line is active
                    line = line.replace("# target", "target").replace("#target", "target")
                else:
                    # Make sure the line is commented out
                    if line[0] != "#":
                        line = "# " + line.strip()

            if line.startswith("[build]"):
                mode = "inbuild"

            config.append(line.strip())

    with open('.cargo/config', 'w') as output_file:
        for line in config:
            output_file.write(line + "\n")


@task(help={
    'program': "Program or example to build & run.",
    'stop':    "Stop execution immediately.",
    'console': "Open console after starting execution.",
})
def run(c, program, stop=False, console=False):
    """Run a program or example in the current environment"""

    path = build(c, program)
    mcu  = env_read()['mcu']

    if mcu == 'qemu':
        cmd = []
        cmd.append("qemu-system-arm")
        cmd.append("-cpu cortex-m3")
        cmd.append("-machine lm3s6965evb")
        cmd.append("-nographic")
        cmd.append("-semihosting-config enable=on,target=native")

        if stop:
            cmd.append("-gdb tcp::3333")
            cmd.append("-S")

        cmd.append("-kernel {}".format(path))

        logger.info("--- Starting QEMU ---")
        c.run(" ".join(cmd))

    else:
        cmd = []
        cmd.append("bobbin")
        cmd.append("run")

        if not console:
            cmd.append("--no-console")

        cmd.append("--example {}".format(program))

        logger.info("--- Flashing ---")
        c.run(" ".join(cmd))
        
        


@task(help={'program': "Program or example to build & run."})
def build(c, program):
    """Build the specified program or example"""

    logger.info("--- Building {} ---".format(program))
    c.run("cargo build --example {}".format(program), pty=True)

    env  = env_read()
    data = yaml.load(open(DEVICES_FILE, 'r'))
    elf  = "target/{}/debug/examples/{}".format(data[env['mcu']]['target'], program)

    # Save the current build target so that other programs
    # know the most recently complied program / example.
    env_save(merge(env, dict(elf=elf)))

    return elf

@task
def debug(c):
    """Enter the debugger for the most recent build"""
    env = env_read()

    cmd = []
    cmd.append("arm-none-eabi-gdb")
    cmd.append("-nx")
    cmd.append("-ex 'target remote :3333'")
    cmd.append("-q {}".format(env['elf']))

    logger.info("--- Starting Debugger ---")
    c.run(" ".join(cmd), pty=True)

@task
def clean(c):
    """Clean up all build results"""
    c.run("cargo clean", pty=True)
