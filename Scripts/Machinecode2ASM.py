#!/usr/bin/env python
# -*- coding:utf-8 -*-
###
# Filename: M2A.py
# Created Date: Wednesday, November 28th 2018, 8:52:37 pm
# Author: Aero
# Usage: 这是一个RV32I指令集机器码的解码器
#        运行示例： ./M2A.py <machinecode_strings_file>
#        思路大概是这样
#        RV32I指令集会根据optcode,func3,func7等等分支出不同的指令
#        有的指令根据optcode即可得出，有的得根据func3,func7再筛选一下
#        为了满足这样一个多种类型的多级嵌套查询，我使用了多级字典
#        相应位置的机器码作为字典的key
#        为了解码需要，又设置了uint_KeyTag，和uint_SftTag，以此记录相应的移位操作和与运算的值
#        在得出具体的指令之后，会根据指令类型进一步解码得出操作数
# -----
# Last Modified: Thu Dec 06 2018
# Modified By: Aero
# ----------------------------
# --->
# HISTORY:
# Date      	By   	Comments
# ----------	-----	----------------------------------------------------------
###
import string 
import sys, getopt

uint_KeyTag = 0xffff #作为字典的一个key 用以查询"与操作"的值
uint_SftTag = 0xfffe #作为字典的一个key 用以查询移位操作的值

# 根据机器码直接给出寄存器名称的字典
dict_RVBaseISAreg = dict({
    0:'x0',
    1:'x1',
    2:'x2',
    3:'x3',
    4:'x4',
    5:'x5',
    6:'x6',
    7:'x7',
    8:'x8',
    9:'x9',
    10:'x10',
    11:'x11',
    12:'x12',
    13:'x13',
    14:'x14',
    15:'x15',
    16:'x16',
    17:'x17',
    18:'x18',
    19:'x19',
    20:'x20',
    21:'x21',
    22:'x22',
    23:'x23',
    24:'x24',
    25:'x25',
    26:'x26',
    27:'x27',
    28:'x28',
    29:'x29',
    30:'x30',
    31:'x31'
})
# 记录指令类型的字典
dict_RVBaseISAinstructionType = dict({
    'ADDI':'I',
    'SLLI':'V',#没有对应的类型 故命名V
    'SRLI':'V',#没有对应的类型 故命名V
    'SRAI':'V',#没有对应的类型 故命名V
    'SLTI':'I',
    'SLTIU':'I',
    'XORI':'I',
    'ORI':'I',
    'ANDI':'I',
    'SB':'S',
    'SH':'S',
    'SW':'S',
    'LB':'I',
    'LH':'I',
    'LW':'I',
    'LBU':'I',
    'LHU':'I',
    'JALR':'I',
    'FENCE':'F',#没有对应的类型 故命名F
    'FENCE.I':'F',#没有对应的类型 故命名F
    'ECALL':'E',#没有对应的类型 故命名E
    'EBREAK':'E',#没有对应的类型 故命名E
    'CSRRW':'C',
    'CSRRS':'C',
    'CSRRC':'C',
    'CSRRWI':'CI',
    'CSRRSI':'CI',
    'CSRRCI':'CI',
    'BEQ':'B',
    'BNE':'B',
    'BLT':'B',
    'BGE':'B',
    'BLTU':'B',
    'BGEU':'B',
    'ADD':'R',
    'SUB':'R',
    'SLL':'R',
    'SLT':'R',
    'SLTU':'R',
    'XOR':'R',
    'SRL':'R',
    'SRA':'R',
    'OR':'R',
    'AND':'R',
    'LUI':'U',
    'AUIPC':'U',
    'JAL':'J'
})

# RV32I指令集
dict_RVBaseISAopcode99 = dict({
    # @[14:12]
    uint_KeyTag:0x00007000,
    uint_SftTag:12,
    0:'BEQ',          #3b000
    1:'BNE',          #3b001
    4:'BLT',          #3b100
    5:'BGE',          #3b101
    6:'BLTU',         #3b110
    7:'BGEU'          #3b111
})

dict_RVBaseISAopcode3 = dict({
    # @[14:12]
    uint_KeyTag:0x00007000,
    uint_SftTag:12,
    0:'LB',          #3b000
    1:'LH',          #3b001
    2:'LW',          #3b100
    4:'LBU',         #3b101
    5:'LHU'         #3b110
})

dict_RVBaseISAopcode35 = dict({
    # @[14:12]
    uint_KeyTag:0x00007000,
    uint_SftTag:12,
    0:'SB',          #3b000
    1:'SH',          #3b001
    2:'SW'          #3b100
})

dict_RVBaseISAopcode19_5 = dict({
    # @[32:25]
    uint_KeyTag:0xfe000000,
    uint_SftTag:25,
    0:'SRLI',             #7b000_0000
    32:'SRAI'            #7b010_0000
})

dict_RVBaseISAopcode19 = dict({
    # @[14:12]
    uint_KeyTag:0x00007000,
    uint_SftTag:12,
    0:'ADDI',                     #3b000
    1:'SLLI',                     #3b001@[14:12],7b000_0000@[31:25]
    2:'SLTI',                     #3b010
    3:'SLTIU',                    #3b011
    4:'XORI',                     #3b100
    5:dict_RVBaseISAopcode19_5,   #3b101
    6:'ORI',                      #3b110
    7:'ANDI'                      #3b111
})

dict_RVBaseISAopcode51_0 = dict({
    # @[32:25]
    uint_KeyTag:0xfe000000,
    uint_SftTag:25,
    0:'ADD',             #7b000_0000
    32:'SUB'            #7b010_0000
})

dict_RVBaseISAopcode51_5 = dict({
    # @[32:25]
    uint_KeyTag:0x00007000,
    uint_SftTag:12,
    0:'SRL',             #7b000_0000
    32:'SRA'            #7b010_0000
})

dict_RVBaseISAopcode51 = dict({
    # @[14:12]
    uint_KeyTag:0x00007000,
    uint_SftTag:12,
    0:dict_RVBaseISAopcode51_0,   #3b000
    1:'SLL',                      #3b001@[14:12],7b000_0000@[31:25]
    2:'SLT',                      #3b010@[14:12],7b000_0000@[31:25]
    3:'SLTU',                     #3b011@[14:12],7b000_0000@[31:25]
    4:'XOR',                      #3b100@[14:12],7b000_0000@[31:25]
    5:dict_RVBaseISAopcode51_5,   #3b101
    6:'OR',                       #3b110@[14:12],7b000_0000@[31:25]
    7:'AND'                       #3b111@[14:12],7b000_0000@[31:25]
})

dict_RVBaseISAopcode15 = dict({
    # @[14:12]
    uint_KeyTag:0x00007000,
    uint_SftTag:12,
    0:'FENCE',             #3b000
    1:'FENCE.I'            #3b001
})


dict_RVBaseISAopcode115_0 = dict({
    # @[31:20]
    uint_KeyTag:0xfff00000,
    uint_SftTag:20,
    0:'ECALL',             #3b000
    1:'EBREAK'            #3b001
})

dict_RVBaseISAopcode115 = dict({
    # @[14:12]
    uint_KeyTag:0x00007000,
    uint_SftTag:12,
    0:dict_RVBaseISAopcode115_0,          #3b000
    1:'CSRRW',                            #3b001
    2:'CSRRS',                            #3b010
    3:'CSRRC',                            #3b011
    5:'CSRRWI',                           #3b101
    6:'CSRRSI',                           #3b110
    7:'CSRRCI'                           #3b111
})

dict_RVBaseISA = dict({
    #opcode@[6:0]
    uint_KeyTag:0x0000007f,
    uint_SftTag:0,
    55:'LUI',                         #7b011_0111
    23:'AUIPC',                       #7b001_0111
    111:'JAL',                        #7b110_1111
    103:'JALR',                       #7b110_0111
    99:dict_RVBaseISAopcode99,        #7b110_0011
    3:dict_RVBaseISAopcode3,          #7b000_0011
    35:dict_RVBaseISAopcode35,        #7b010_0011
    19:dict_RVBaseISAopcode19,        #7b001_0011
    51:dict_RVBaseISAopcode51,        #7b011_0011
    15:dict_RVBaseISAopcode15,        #7b000_1111
    115:dict_RVBaseISAopcode115,      #7b111_0011
    })



uint32s_MachineCodeLine = [] #

strs_MachineCodeLine = []



def predealMachineCodelines(filepath):
    # 分出操作数和操作指令
    src = open(filepath,"r")
    strs_MachineCodeLine = src.readlines()
    for line in strs_MachineCodeLine:
        str_line = str(line)
        str_line =  str_line.strip("\n")
        uint32s_MachineCodeLine.append(int(str_line,16))
    pass



def printISA(dict_n):
    for k in dict_n.keys():
        if isinstance(dict_n[k],dict):
            printISA(dict_n[k])
        elif not isinstance(dict_n[k],int):
            print "'" + str(dict_n[k]) + "':''," 


def getInstruction(int_code,dict_isa):
    int_key = dict_isa[uint_KeyTag]
    int_sft = dict_isa[uint_SftTag]
    op = dict_isa[(int_code & int_key) >> int_sft]
    c = int_code
    if isinstance(op,dict):
        op = getInstruction(int_code,op)
        return str(op)
    else:
        return str(op)

def parseUType(int_machinecode):
    int_imm = int_machinecode >> 12
    str_imm = "IMM:%#08x"%int_imm

    int_rd = (int_machinecode & 0x00000f80) >> 7
    str_tag_rd = dict_RVBaseISAreg[int_rd]

    str_result = "RD:" + str_tag_rd + "," + str_imm
    return str_result


def parseRType(int_machinecode):
    int_rd  = (int_machinecode & 0x00000f80) >> 7
    str_tag_rd = dict_RVBaseISAreg[int_rd]

    int_rs1 = (int_machinecode & 0x000f8000) >> 15
    str_tag_rs1 = dict_RVBaseISAreg[int_rs1]

    int_rs2 = (int_machinecode & 0x01f00000) >> 20
    str_tag_rs2 = dict_RVBaseISAreg[int_rs2]

    str_result = "RD:" + str_tag_rd + "," + "RS1:" + str_tag_rs1 + "," + "RS2:" + str_tag_rs2

    return str_result

def parseIType(int_machinecode):
    int_imm = int_machinecode >> 20
    str_imm = "IMM:%#08x"%int_imm

    int_rd  = (int_machinecode & 0x00000f80) >> 7
    str_tag_rd = dict_RVBaseISAreg[int_rd]

    int_rs1 = (int_machinecode & 0x000f8000) >> 15
    str_tag_rs1 = dict_RVBaseISAreg[int_rs1]
    

    str_result = "RD:" + str_tag_rd + "," + "RS1:" + str_tag_rs1 + "," +  str_imm
    
    return str_result


def parseCType(int_machinecode):
    int_rd  = (int_machinecode & 0x00000f80) >> 7
    str_tag_rd = dict_RVBaseISAreg[int_rd]

    int_rs1 = (int_machinecode & 0x000f8000) >> 15
    str_tag_rs1 = dict_RVBaseISAreg[int_rs1]
    
    int_csr = int_machinecode >> 20
    str_csr = "CSE:%#08x"%int_csr

    str_result = "RD:" + str_tag_rd + "," + "RS1:" + str_tag_rs1 + "," +  str_csr
    
    return str_result

def parseCIType(int_machinecode):
    int_rd  = (int_machinecode & 0x00000f80) >> 7
    str_tag_rd = dict_RVBaseISAreg[int_rd]

    int_zimm = (int_machinecode & 0x000f8000) >> 15
    str_zimm = "ZIMM:%#08x"%int_zimm
    
    int_csr = int_machinecode >> 20
    str_csr = "CSE:%#08x"%int_csr

    str_result = "RD:" + str_tag_rd + "," +  str_zimm + "," +  str_csr
    
    return str_result

def parseSType(int_machinecode):
    int_imm4_0 = (int_machinecode & 0x00000f80) >> 7
    int_imm11_5 = (int_machinecode >> 25) << 5
    int_imm = (int_imm11_5 & int_imm4_0) & 0x0fff
    str_imm = "IMM:%#08x"%int_imm

    int_rs1 = (int_machinecode & 0x000f8000) >> 15
    str_tag_rs1 = dict_RVBaseISAreg[int_rs1]

    int_rs2 = (int_machinecode & 0x01f00000) >> 20
    str_tag_rs2 = dict_RVBaseISAreg[int_rs2]

    str_result = "RS1:" + str_tag_rs1 + "," + "RS2:" + str_tag_rs2 + "," + str_imm

    return str_result


def parsJType(int_machinecode):
    int_imm20 = (int_machinecode >> 31) << 19
    int_imm19_12 = ((int_machinecode >> 12) & 0x000ff) << 11
    int_imm11 = ((int_machinecode >> 20) & 0x00001) << 10
    int_imm10_1 = ((int_machinecode >> 21) & 0x01ff) 
    int_imm = int_imm20 | int_imm19_12 | int_imm11 | int_imm10_1
    str_imm = "IMM:%#08x"%int_imm

    int_rd  = (int_machinecode & 0x00000f80) >> 7
    str_tag_rd = dict_RVBaseISAreg[int_rd]

    str_result = "RD:" + str_tag_rd +  "," + str_imm

    return str_result

def parseVType(int_machinecode):
    int_rd  = (int_machinecode & 0x00000f80) >> 7
    str_tag_rd = dict_RVBaseISAreg[int_rd]

    int_rs1 = (int_machinecode & 0x000f8000) >> 15
    str_tag_rs1 = dict_RVBaseISAreg[int_rs1]

    int_shamt = (int_machinecode & 0x01f00000) >> 20
    str_shamt = "SHAMT: %#08x"%int_shamt

    str_result = "RD:" + str_tag_rd + "," + "RS1:" + str_tag_rs1 + "," + str_shamt

    return str_result

def parseEType(int_machinecode):
    return " "





def parseOpts(int_machinecode,str_op):
    optype = dict_RVBaseISAinstructionType[str_op]
    opcontent = ""
    
    if optype == 'CI':
        opcontent = parseCIType(int_machinecode)
    elif optype == 'C':
        opcontent = parseCType(int_machinecode)
    elif optype == 'E':
        opcontent = parseEType(int_machinecode)
    elif optype == 'I':
        opcontent = parseIType(int_machinecode)
    elif optype == 'R':
        opcontent = parseRType(int_machinecode)
    elif optype == 'S':
        opcontent = parseSType(int_machinecode)
    elif optype == 'U':
        opcontent = parseUType(int_machinecode)
    elif optype == 'V':
        opcontent = parseVType(int_machinecode)
    else:
        opcontent = "ERROR!!!"
    
    return opcontent



if __name__ == "__main__":
    # printISA(dict_RVBaseISA)
    inputfile = sys.argv[1]
    predealMachineCodelines(inputfile)
    for uint_single_machinecodeline in uint32s_MachineCodeLine:
        str_single_machinecodeline = '0x%08x'%uint_single_machinecodeline
        str_asm_instruction = getInstruction(uint_single_machinecodeline,dict_RVBaseISA)
        print "----------------------------------"
        print str_single_machinecodeline + "  #" + str_asm_instruction + " " + parseOpts(uint_single_machinecodeline,str_asm_instruction)
        print "----------------------------------"


