import argparse
import os
import sys
import subprocess
from lexer import minic_lexer as lexer
from parser import minic_parser as parser
from preprocessor import preprocessor
from IRGen import IRGen
import xml.etree.ElementTree as ET
from wat import Wat
from typeChecker import TypeChecker

class watc():
    lexer: lexer
    parser: parser
    preprocessor: preprocessor
    processed_data: str

    def __init__(self, files: list[str], verify: str = None, output: str = None, run_type: str = None, run: bool = True, type_check: bool = False, type_check_only=False, optimize: bool = False):
        # Process any of include or define before we pass it into our lexer
        file_data = {}
        self.typeCheck = True if type_check == 'True' else False
        self.run = True if run == 'True' else False
        self.type_check_only = True if type_check_only == 'True' else False
        self.optimize = True if optimize == 'True' else False
        # Preprocessor loading
        for file_path in files:
            file = open(file_path, "r")
            lines = file.readlines()
            file.close()
            lines = [l.replace("\n", "") for l in lines]
            file_data.setdefault(file_path.split('/')[-1], lines)

        # Building everything from preprocessor, lexer to parser regardless of type
        # Preprocessor check
        try:
            self.processed_data = '\n'.join(preprocessor(file_data))
        except Exception as e:
            print("One of the file provided has an invalid syntax when being preoprocessed")
            print("Error: " + str(e))
            print("Now aborting...")
            return
        # Lexer building
        try:
            self.lexer = lexer()
            self.lexer.build()
        except Exception as e:
            print("One of the file provided has an invalid syntax when being lexed")
            print("Error: " + str(e))
            print("Now aborting...")
            return
        # Parser building
        try:
            self.parser = parser()
            self.parser.build()
            root = self.parser.parse(self.processed_data)
        except Exception as e:
            print("One of the file provided has an invalid syntax when being parsed")
            print("Error: " + str(e))
            print("Now aborting...")
            return
        # We got rid of IRGen for this sprint as found it more difficult
        # self.irgen = IRGen()
        # self.irgen.generate(root)

        # Typechecking
        if self.typeCheck or self.type_check_only:
            self.typeChecker = TypeChecker(self.processed_data)
            self.typeChecker.check(root)
            self.typeChecker.print_errors()
            if self.type_check_only:
                if not self.typeChecker.has_errors():
                    print("No type errors")
                return

        # Generating final output
        try:
            self.wat = Wat(self.optimize)
            self.wat.generate(root)
        except Exception as e:
            print("One of the file provided has an invalid syntax when being converted to wat")
            print("Error: " + str(e))
            print("Now aborting...")
            return

        match run_type:
            case 'all' | 'wat':
                filename = output
                if not output:
                    filename = 'out.wat'
                f = open(filename, 'w')
                self.wat.write_wat(f)

            case 'parser':
                res = self.parser.generate_xml(self.processed_data)
                filename = output
                if not output or output == 'default.wat':
                    filename = 'parser.xml'
                with open(filename, 'w') as f:
                    tree = ET.ElementTree(res)
                    tree.write(f, encoding='unicode')
            case 'preprocessor':
                filename = output
                if not filename:
                    filename = 'preprocessed.c'
                with open(filename, 'w') as f:
                    f.write(self.processed_data)
            case 'irgen':
                print('This feature has been deprecated')
                return
        # If output is specified
        match verify:
            case 'lexer':
                self.lexer.test(self.processed_data)
            case 'parser':
                self.parser.test(self.processed_data)
            case 'xml':
                res = self.parser.generate_xml(self.processed_data)
                if output:
                    with open(output, 'w') as f:
                        tree = ET.ElementTree(res)
                        tree.write(f, encoding='unicode')
                else:
                    print(ET.dump(res))
            case 'ir':
                print('This feature has been deprecated')
                return
            case 'wat':
                if output:
                    with open(output, 'w') as f:
                        self.wat.write_wat(f)
                else:
                    self.wat.print_wat()
            case 'wasm':
                if output is None:
                    wat_name = "out.wat"
                    wasm_name = "out.wasm"
                else:
                    wasm_name = output
                    wat_name = output[:-4] + "wat"

                cmd = 'cp out.wat client/'
                cur_dir = os.getcwd()
                os.chdir(f'{cur_dir}/client/')
                with open(wat_name, 'w') as f:
                    self.wat.write_wat(f)

                #cmd = '../wabt/bin/wat2wasm ' + wat_name + ' --output=' + wasm_name
                cmd = 'npx wat2wasm ' + wat_name + f' --output="{wasm_name}"'
                print("Running wat2wasm and assembling .wat to .wasm: ", cmd)
                os.system(cmd)

                if self.run:
                    node_cmd = f'node index.js --input="{wasm_name}"'
                    print("Loading and executing .wasm: ", node_cmd)
                    os.system(node_cmd)
                os.chdir(cur_dir)


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description='Take in the miniC source code and compile into specified format.',
                                         formatter_class=argparse.RawTextHelpFormatter)

    def file_checker(choices, fname):
        ext = os.path.splitext(fname)[1][1:]
        if ext not in choices:
            arg_parser.error(
                "One of the file doesn't end with extension: {}".format(choices))

        if not os.path.isfile(fname):
            arg_parser.error("File {} doesn't exist".format(fname))
        return fname

    arg_parser.add_argument('FILE', help="Input files with miniC source code (only c extension is accepted)",
                            type=lambda s: file_checker(("c"), s), nargs='+')
    arg_parser.add_argument(
        '-o',
        '--output',
        help="Name of the output file to compile to."
    )
    arg_parser.add_argument(
        '-t',
        '--type',
        help='Type of compilers:\nall: Compiles into .wat file\nlexer: Execute both Preprocessor and Lexer\n' +
            'parser: Execute Preprocessor, lexer and parser to generate a AST in XML format\n' +
            'ir: Generate an easily readable 3ac code (DEPRECATED)\n' +
            'wat: Generate a wat file\n' +
            'wasm: Generate a wasm file',
        default="all",
        choices=("all", "lexer", "parser", "preprocessor", "ir", "wat", "wasm"))

    arg_parser.add_argument(
        '-v',
        '--verify',
        help='Verify the output of the compiler, either the lexer, parser, IR, wat or wasm',
        choices=("parser", "lexer", "xml", "ir", "wat", "wasm"))

    arg_parser.add_argument(
        '-tc',
        '--type-check',
        help='Type check the output of the compiler',
        choices=('True', 'False'),
        default='False'
    )
    arg_parser.add_argument(
        '-r',
        '--run-prog',
        help='Compile .wasm binary and run it',
        choices=('True', 'False'),
        default='True'
    )
    arg_parser.add_argument(
        '-tco',
        '--type-check-only',
        help='Only run type checker',
        choices=('True', 'False'),
        default='False'
    )

    arg_parser.add_argument(
        '-op',
        '--optimize',
        help='Turn optimizations on or off',
        choices=('True', 'False'),
        default='False'
    )

    args = arg_parser.parse_args()
    if len(sys.argv) < 2:
        arg_parser.print_help()
        sys.exit(1)

    m = watc(args.FILE, verify=args.verify, run_type=args.type, run=args.run_prog, output=args.output, type_check=args.type_check, type_check_only=args.type_check_only, optimize=args.optimize)
