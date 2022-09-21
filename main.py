import sys
sys.path.insert(0, 'src')
import argparse
from platforms.app import App


parser = argparse.ArgumentParser()
parser.add_argument('--input', '-i', default='samples/sample.3.json')
args = parser.parse_args()

app = App()
app.read_input(args.input, weight=False)

_, min_makespan, max_usage = app.schedule('heft')
print(min_makespan, max_usage)

_, makespan, usage = app.schedule('heft_delay', 435)
print(makespan, usage)
