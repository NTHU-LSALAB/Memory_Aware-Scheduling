import sys
sys.path.insert(0, 'src')
sys.path.insert(0, './')
from converter import converter
from platforms.app import App
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--input', '-i', default='samples/size/sample.15.json')
args = parser.parse_args()

algorithm = 'ippts'  # heft, cpop, ippts
app = App()
dag_like = converter(args.input)
app.read_input(dag_like, weight=False, format='mb')

_, min_makespan, max_usage = app.schedule(algorithm)
print(min_makespan, max_usage)

_, makespan, usage = app.schedule(algorithm+'_delay', 150)
print(makespan, usage)

_, makespan, usage = app.schedule(
    algorithm+'_reserve', 115, {'depth': 1, 'suffix': '-1'})
print(makespan, usage)
