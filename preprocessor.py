import re


define_reg = re.compile("^\s*#define (\w+) (\w+)\s*$")
include_reg = re.compile('^\s*#include "(\w+\.c)"\s*$')
comment_reg = re.compile("(.*)\/\/(.*)")
mainfunc_reg = re.compile("int(\s+)main")
hashtag_reg = re.compile("#")

defined = {}

def process_line(line: str) -> str:
    for de in defined:
        reg = defined[de][0]
        res = reg.match(line)
        if not res:
           continue

        groups = res.groups() 
        line = groups[0] + defined[de][1] + groups[2] 
    return line

def process_file(cfiles: dict, name:str) -> list[str]:
    r = []
    state = 0
    try:
        for line in cfiles[name]:
            if line.isspace() or line == "":
                continue

            include_res = include_reg.match(line)
            define_res = define_reg.match(line)
            comment_res = comment_reg.match(line)
            hashtag_res = hashtag_reg.match(line)

            if include_res:
                if(state!=0):
                    raise Exception("Include")

                included_file = include_res.groups()[0]
                r += process_file(cfiles, included_file) 

            elif define_res:
                if state == 2:
                    raise Exception("Define")

                if state == 0:
                    state = 1

                if define_res.groups()[0] in defined:
                    raise Exception("Double define")

                custom_reg = re.compile("(.*)(" + define_res.groups()[0] + ")(.*)")
                defined[define_res.groups()[0]] = (custom_reg, define_res.groups()[1])
            
            elif hashtag_res:
                raise Exception("Header tag in wrong format")

            elif comment_res:
                if comment_res.groups()[0].isspace() or comment_res.groups()[0] == "":
                    continue

                if state != 2:
                    state = 2

                r += [process_line(comment_res.groups()[0])]
            else:
                if state != 2:
                    state = 2
                r += [process_line(line)]
    except KeyError as e:
        print(f'Error: Missing file {e} as one of the input files')
    except Exception as e:
        print(f'Error: {e}')
    return r


def preprocessor(cfiles: dict) -> list[str]:
    files_with_main = []
    for f in cfiles:
        for line in cfiles[f]:
            if mainfunc_reg.match(line):
                files_with_main.append(f)

    if len(set(files_with_main)) != 1:
        raise Exception("Wrong number of main files")

    return process_file(cfiles, files_with_main[0])

