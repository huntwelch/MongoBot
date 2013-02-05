import inspect

def serotonin(cortex, expansion):
    methods = inspect.getmembers(expansion)
    letter = expansion.category[:1]
    word = expansion.category[1:]

    helps = []

    for name, method in methods:
        if not hasattr(method, "create_command"):
            continue

        if hasattr(method, "help"):
            helps.append("~" + name + " " + method.help)

        cortex.commands[name] = method
        if len(helps):
            cortex.helpmenu[letter] = helps
            cortex.helpcategories = "(" + letter ")" + word
        
def category(text):
    def add(cls):
        cls.category = text
        return cls
    return add 

def axon(fn):
    fn.create_command = True 
    return fn

def help(text):
    def add(fn):
        fn.help = text
        return fn
    return add 

        

