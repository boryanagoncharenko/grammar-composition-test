from pathlib import Path
from lark import Lark
from lark.visitors import Transformer, merge_transformers


__dir__ = Path(__file__).parent


def hash_var(var):
    return var


class ConvertToPython(Transformer):
    def __init__(self):
        super().__init__()

    def start(self, args):
        return args[0]

    def program(self, args):
        return '\n'.join([str(c) for c in args])

    def command(self, args):
        return args[0]

    def text(self, args):
        return ''.join(args)

    def is_variable(self, name):
        return False

    def sleep_after(self, commands, indent=True):
        lines = commands.split()
        if lines[-1] == "time.sleep(0.1)":  # we don't sleep double so skip if final line is a sleep already
            return commands

        sleep_command = "time.sleep(0.1)" if indent is False else "  time.sleep(0.1)"
        return commands + "\n" + sleep_command


class ConvertToPython_1(ConvertToPython):
    def __init__(self):
        super().__init__()
        __class__.level = 1

    def error_invalid(self, args):
        return 'INVALID NODE!'

    def program(self, args):
        return '\n'.join([str(c) for c in args])

    def command(self, args):
        return args[0]

    def text(self, args):
        return ''.join([str(c) for c in args])

    def integer(self, args):
        return str(args[0])

    def number(self, args):
        return str(args[0])

    def print(self, args):
        # escape needed characters
        argument = args[0]
        return "print('" + argument + "')"

    def ask(self, args):
        argument = args[0]
        return "answer = input('" + argument + "')"

    def echo(self, args):
        if len(args) == 0:
            return "print(answer)"  # no arguments, just print answer

        argument = args[0]
        return "print('" + argument + " '+answer)"

    def forward(self, args):
        if len(args) == 0:
            return self.make_forward(50)

        parameter = int(args[0])
        return self.make_forward(parameter)

    def make_forward(self, parameter):
        return self.sleep_after(f"t.forward({parameter})", False)

    def test(self, args):
        return 'transpiled in level 1'

    def turn(self, args):
        if len(args) == 0:
            return "t.right(90)"  # no arguments defaults to a right turn

        arg = args[0]
        if self.is_variable(arg) or arg.isnumeric():
            return f"t.right({arg})"
        elif arg == 'left':
            return "t.left(90)"
        elif arg == 'right':
            return "t.right(90)"
        else:
            # the TypeValidator should protect against reaching this line:
            raise Exception('Something went wrong')


class ConvertToPython_2(ConvertToPython):
    def __init__(self):
        super().__init__()
        __class__.level = 2

    def test(self, args):
        return 'transpiled in level 2'

    def ask(self, args):
        var = args[0]
        all_parameters = ["'" + a + "'" for a in args[1:]]  # lacks processing
        return f'{var} = input(' + '+'.join(all_parameters) + ")"

    def var(self, args):
        return args[0]


class ConvertToPython_3(ConvertToPython):
    def __init__(self):
        super().__init__()
        __class__.level = 3

    def test(self, args):
        return 'transpiled in level 3'


level_1_parser = Lark.open("level1-Total.lark", rel_to=__file__)
level_2_parser = Lark.open("level2-Total.lark", rel_to=__file__)
level_3_parser = Lark.open("level3-Total.lark", rel_to=__file__)


def base():
    return merge_transformers(ConvertToPython(), level1=ConvertToPython_1(), error=ConvertToPython_1())


# These correspond to the files for level grammars. The base transformer is the level transformer
# and the imported grammars need to be included with the corresponding namespace
l2 = merge_transformers(ConvertToPython_2(), level1=ConvertToPython_1())
l3 = merge_transformers(ConvertToPython_3(), level2=l2)

# There correspond to the *-Total grammar files. They need a base grammar which can parse a program
# and they need to use namespaces for every grammar imported in the *-Total file.
level_1_transpiler = base()
level_2_transpiler = merge_transformers(base(), level2=l2)
level_3_transpiler = merge_transformers(base(), level2=l2, level3=l3)

level_to_lark = {1: (level_1_parser, level_1_transpiler),
                 2: (level_2_parser, level_2_transpiler),
                 3: (level_3_parser, level_3_transpiler)}


def transpile(level, input_string):
    print('-----------INPUT-----------')
    print(input_string)
    if level not in level_to_lark.keys():
        raise Exception(f'This demo supports only levels 1-3. Level {level} is not supported.')

    (parser, transpiler) = level_to_lark[level]

    parse_tree = parser.parse(input_string)
    print('-----------PARSED----------')
    print(parse_tree.pretty(indent_str='    '))

    print('---------TRANSPILED--------')
    transpiled = transpiler.transform(parse_tree)
    print(transpiled)


def main():
    transpile(3, """
turn 180
ask What is your name?
var is ask whatis your name?
test1 aaa
test2 bbb
test3 ccc
whasfjdskfj
""")


if __name__ == "__main__":
    main()

