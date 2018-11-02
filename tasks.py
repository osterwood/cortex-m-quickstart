import pystache
import yaml

from invoke import task

def merge(x, y):
    z = x.copy()
    z.update(y)
    return z

@task(help={'mcu': "Processor to re-target for"})
def target(c, mcu):

    data = yaml.load(open('devices.yml', 'r'))
    meta = {'mcu': mcu}

    if mcu not in data.keys():
        print("MCU '{}' is not recognized. Select from:".format(mcu))
        print("  " + ", ".join(sorted(data.keys())))
        return

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
            if line.startswith("[target."):
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
