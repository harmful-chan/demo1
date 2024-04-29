import os
import re

def multi_line_input():
    with open(r'\Desktop\记录.txt', 'r', encoding='utf-8') as fr:
        text = fr.readlines()
    return text


multiline_string = multi_line_input()
with open(r'\Desktop\res.txt', 'w', encoding='utf-8') as fw:
    for index, i in enumerate(multiline_string):
        res = re.findall(r'(扣除金额)：.*?\s*(\b\d+-\d+-\d+-\d+\s+\d+\.\d+RMB\b|$)| (.* occurred).*', i)
        # print(res)
        if len(res) == 0:
            fw.write('搜不到订单\n')
            continue
        if res[0][-1] != '':
            fw.write('失败\n')
            continue
        if res[0][1] == '':
            fw.write('余额不足\n')
            continue

        cost = res[0][1].split()[-1]
        text = ''
        if cost == 0:
            text = '成本异常'
        else:
            text = '\t'.join(res[0][1].split())

        if index < len(multiline_string)-1:
            fw.write(text + '\n')
        else:
            fw.write(text)

    os.startfile(r'\Desktop\res.txt')