'''
toml文件不能处理[(a, b)]数据，需要删除括号
'''
import os


def del_bracket():
    files = [f for f in os.listdir('.') if os.path.isfile(f)]
    file_urls = []
    for f in files:
        if '.toml' in f and f[:9] != 'readable_':
            print(f'找到文件{f}')
            file_urls.append(f)
    for i in file_urls:
        with open(i, 'r') as f:
            content = f.readlines()
            for line in content:
                if len(line) > 5:
                    print(0, type(line))
                    line = line.replace('(', '')
                    line = line.replace(')', '')
                    # print(line)
                    with open('readable_' + i, 'w') as new_f:
                        new_f.write(line)
                        
del_bracket()
