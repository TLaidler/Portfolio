#!/bin/bash
########################################################################################################################################################
# Bem vindo                                                                                                                                            #
# colocar na pasta binário do sistema                                                                                                                  #
# sudo cp ~/endereco/Questao3.sh /bin                                                                                    #
########################################################################################################################################################
# Criação de script para renomear todos os arquivos de um determinado diretório, a ser escolhido, baseado em um padrão de início e um de fim,          #
# onde o usuário escolhe se é de início ou de fim (use os comandos read e if)                                                                          #
########################################################################################################################################################


if [ "$1" == "" ];
then
    echo "Bem vindo!!"
    echo "Esse script renomeia todos os arquivos e pastas do diretório que você escolher"
    echo "Adicionando um prefixo e um sufixo"
    echo "Modo de uso:"
    echo "Coloque o caminho desejado como parâmetro. Se quiser, pode usar a tecla TAB para ajudar."
    echo "Exemplo> $0 /home/usuario/Documentos" 
    echo "Adiante será exibido o menu de opções. Bastando escolher o número referente a função desejada."
else
    cd $@

opcoes=("Listar tudo" "Renomear inicio" "Renomear final" "Sair")

select isso in "${opcoes[@]}"
 do
  case $isso in
       "Listar tudo")
         echo "Você escolheu listas os arquivos e pastas deste diretório!"
         ls
         ;;
       "Renomear inicio")
         echo "Você escolheu renomear o início dos arquivos e diretórios dentro do caminho especificado anteriormente"
         echo "O que deseja add no inicio de cada arquivo e pasta?"
         echo "Exemplo: Quero colocar Módulo1 no início, logo um arquivo aula1.mp4 ficará Módulo1-aula1.mp4" 
         echo "Obs: o - será add automaticamente, separando o início adicionado do nome original"
         read new;
         for meuarquivo in * ; 
         do novonome="$new-$meuarquivo"; 
         mv "$meuarquivo" "$novonome"; 
         done         
         ;;
        "Renomear final")
          echo "Você escolheu renomear o final dos diretórios e arquivos dentro do caminho especificado anteriormente"
          echo "O que deseja add no final de cada arquivo ou pasta listado?"
          echo "Exemplo: Quero colocar Módulo1 no final de cada pasta e arquivo, logo uma pasta /Exercícios ficará /Exercícios-Módulo1"
          echo "Obs: o - será add automaticamente. O complemento ocorre depois da extensão dos arquivos. Ou seja, eita.jpg com uia ficaria eita.jpg-uia"
          read news;
          for arquivos in * ;
          do novo="$arquivos-$news"; 
          mv "$arquivos" "$novo"; 
          done
         ;;
        "Sair")
          break
         ;;
        *) echo "opção não reconhecida. Favor, digitar o número correspondente a sua escolha.";;
  esac
 done
fi
