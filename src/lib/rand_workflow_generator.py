from .generator import workflows_generator
import json

def main():
    dag = workflows_generator('rand', 300)
    with open('rand_workflow.json', 'w') as f:
        json.dump({
            "nodes": dag['nodes'],
            "edges": dag['edges'],
        }, f, indent=4)

if __name__ == '__main__':
    main()