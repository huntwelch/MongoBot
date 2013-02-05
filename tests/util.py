import inspect

def serotonin(cortex, expansion):
    methods = inspect.getmembers(expansion)
    for name, method in methods:
        if not hasattr(method, "create_command"):
            continue
        cortex.commands[name] = method
        

def axion(fn):
    fn.create_command = True 
    return fn



        

