def funcao1(a, b):
    return a + b + b + a

def funcao2(nome, idade):
    x = (idade *  4 + 8) * 60
    x = (x / 240 + 22) - idade

    return "Parabens " + nome + "! Seu numero da sorte eh " + str(x) + "!"

def funcao3(str1, str2):
    return str1[5:] + str2[:-10]

def funcao4(s, x, i):
    return s[0:i] + x + s[i+1:]

def funcao5(str_s):
    meio = len(str_s) / 2
    return str_s[:meio] + str_s + str_s[meio:]

def funcao6(str_s):
    meio = len(str_s) / 2
    return "#" + str_s[:meio] + "#" + str_s[meio:] + "#"

def funcao7(str_s):
    str_s = str_s[3:] + str_s[:3]
    return str_s

def funcao8(a, b):  
  nova_a = b[:2] + a[2:]  
  nova_b = a[:2] + b[2:]  
  return nova_a + ' ' + nova_b  

    
