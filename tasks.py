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
