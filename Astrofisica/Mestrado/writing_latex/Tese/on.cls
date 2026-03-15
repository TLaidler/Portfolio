%%
%% This is file `on.cls',
%% generated with the docstrip utility.
%%
%% The original source files were:
%%
%% on.dtx  (with options: `class')
%%
%% This is the 'ON' document class used for composition of LaTeX
%% monographs (master and PhD thesis, and PhD qualifying exams)
%% satisfying the requirements of the CPGG-Geophysics.
%%
%% Copyright (C) 2014 Leandro Di Bartolo
%%
%% This program was developed using the COPPE codument class developed
%% by Vicente Helano and George Ainsworth for the COPPETEX projetc
%% website: http://coppetex.sourceforge.net/
%%
%% This program is free software; you can redistribute it and/or modify
%% it under the terms of the GNU General Public License version 3 as
%% published by the Free Software Foundation.
%%
%% This program is distributed in the hope that it will be useful,
%% but WITHOUT ANY WARRANTY; without even the implied warranty of
%% MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
%% GNU General Public License version 3 for more details.
%%
%% You should have received a copy of the GNU General Public License
%% version 3 along with this package (see COPYING file).
%% If not, see <http://www.gnu.org/licenses/>.
%%
%% Author: Leandro Di Bartolo
%%
%% \CheckSum{1417}
%% \CharacterTable
%%  {Upper-case    \A\B\C\D\E\F\G\H\I\J\K\L\M\N\O\P\Q\R\S\T\U\V\W\X\Y\Z
%%   Lower-case    \a\b\c\d\e\f\g\h\i\j\k\l\m\n\o\p\q\r\s\t\u\v\w\x\y\z
%%   Digits        \0\1\2\3\4\5\6\7\8\9
%%   Exclamation   \!     Double quote  \"     Hash (number) \#
%%   Dollar        \$     Percent       \%     Ampersand     \&
%%   Acute accent  \'     Left paren    \(     Right paren   \)
%%   Asterisk      \*     Plus          \+     Comma         \,
%%   Minus         \-     Point         \.     Solidus       \/
%%   Colon         \:     Semicolon     \;     Less than     \<
%%   Equals        \=     Greater than  \>     Question mark \?
%%   Commercial at \@     Left bracket  \[     Backslash     \\
%%   Right bracket \]     Circumflex    \^     Underscore    \_
%%   Grave accent  \`     Left brace    \{     Vertical bar  \|
%%   Right brace   \}     Tilde         \~}
%%
\def\filename{on.dtx}
\def\fileversion{v2.2}
\def\filedate{2011/02/08}
\NeedsTeXFormat{LaTeX2e}[1995/12/01]
\ProvidesClass{on}[\filedate\ \fileversion\ ON Dissertations and Thesis]
\LoadClass[12pt,a4paper,twoside]{book}
\RequirePackage[sort&compress]{natbib}
\RequirePackage{hyphenat}
\RequirePackage{lastpage}
\RequirePackage[english,brazil]{babel}
\RequirePackage{ifthen}
\RequirePackage{graphicx}
\RequirePackage{setspace}
\RequirePackage{tabularx}
\RequirePackage{eqparbox}
\RequirePackage{ltxcmds}
\RequirePackage{url}
\RequirePackage{stringstrings}
\RequirePackage[a4paper,bindingoffset=0.0cm,vcentering=true,%
top=2.5cm,bottom=2.5cm,inner=3.0cm,outer=2.0cm,verbose]{geometry}
\def\ONTeX{{\rm C\kern-.05em{\sc o\kern-.025em p\kern-.025em
p\kern-.025em e}}\kern-.08em
T\kern-.1667em\lower.5ex\hbox{E}\kern-.125emX\spacefactor1000}
\newboolean{maledoc}
\setboolean{maledoc}{false}
\newboolean{doutboolean}
\setboolean{doutboolean}{false}

\DeclareOption{msc}{%
  \newcommand{\@degree}{Ms.}
  \newcommand{\foreign@degree}{M.Sc.}
  \newcommand{\@degreename}{Mestrado}
  \newcommand{\local@degname}{Mestre}
  \newcommand{\foreign@degname}{Master}
  \setboolean{doutboolean}{false}
  \newcommand\local@doctype{Disserta{\c c}{\~ a}o}
  \newcommand\foreign@doctype{Dissertation}
}

\DeclareOption{dscexam}{%
  \newcommand{\@degree}{Dr.}
  \newcommand{\foreign@degree}{Ph.D.}
  \newcommand{\@degreename}{Doutorado}
  \newcommand{\local@degname}{Doutor}
  \newcommand{\foreign@degname}{Doctor}
  \setboolean{maledoc}{true}
  \newcommand\local@doctype{Exame de Qualifica{\c c}{\~ a}o}
  \newcommand\foreign@doctype{Qualifying Exam}
}

\DeclareOption{dsc}{%
  \newcommand{\@degree}{Dr.}
  \newcommand{\foreign@degree}{Ph.D.}
  \newcommand{\@degreename}{Doutorado}
  \newcommand{\local@degname}{Doutor}
  \newcommand{\foreign@degname}{Doctor}
  \setboolean{doutboolean}{true}
  \newcommand\local@doctype{Tese}
  \newcommand\foreign@doctype{Thesis}
}

\DeclareOption{numbers}{%
  \PassOptionsToPackage{numbers}{natbib}
}
\onehalfspacing
\DeclareOption{doublespacing}{%
  \doublespacing
}
\ProcessOptions\relax

\newcommand\department[1]{%
  \ifthenelse{\equal{#1}{COPAA}}
    {\global\def\local@deptname{Astronomia}
     \global\def\foreign@deptname{Astronomy}}{}
  \ifthenelse{\equal{#1}{COGEO}}
    {\global\def\local@deptname{Geof{\'\i}sica}
     \global\def\foreign@deptname{Geophysics}}{}
}

\renewcommand\title[1]{%
  \global\def\local@title{#1}%
}

\newcommand\acknowledgments{\chapter*{\LARGE Agradecimentos}}

\newcommand\foreigntitle[1]{%
  \global\def\foreign@title{#1}%
}

\newcommand\advisor[4]{%
  \global\def\@advtitle{#1}
  \global\def\@advname{#2}
  \global\def\@advsurn{#3}
  \global\def\@advinst{#4}
}

\newcount\@coadvisor\@coadvisor0
\newcommand\coadvisor[4]{%
  \global\@namedef{ONcoAdvisorTitle:\expandafter\the\@coadvisor}{#1}
  \global\@namedef{ONcoAdvisorName:\expandafter\the\@coadvisor}{#2}
  \global\@namedef{ONcoAdvisorSurname:\expandafter\the\@coadvisor}{#3}
  \global\@namedef{ONcoAdvisorInst:\expandafter\the\@coadvisor}{#4}
  \global\advance\@coadvisor by 1
  \ifnum\@coadvisor>1
    \renewcommand\local@coadvisorstring{Co-orientadores}
    \renewcommand\foreign@coadvisorstring{Co-advisors}
  \fi
}

\newcount\@examiner\@examiner0
\newcommand\examiner[3]{%
  \global\@namedef{ONExaminerName:\expandafter\the\@examiner}{#1\ #2}
  \global\@namedef{ONExaminerInst:\expandafter\the\@examiner}{#3}
  \global\advance\@examiner by 1
}

\renewcommand\author[2]{%
  \global\def\@authname{#1}
  \global\def\@authsurn{#2}
}

\global\def\@lcutter{\substring{\@authsurn}{1}{1}}
\newcommand\cutter[1]{\global\def\@ncutter{#1}}
\newcommand\cducode[1]{\global\def\@ncdu{#1}}

\renewcommand\date[3]{%
  \day=#1
  \month=#2
  \year=#3
}

\newcommand\blankpage{\clearpage\thispagestyle{empty}
  \addtocounter{page}{-1}\null\clearpage}

\newcommand\local@monthname{\ifcase\month\or
  Janeiro\or Fevereiro\or Mar{\c c}o\or Abril\or Maio\or Junho\or
  Julho\or Agosto\or Setembro\or Outubro\or Novembro\or Dezembro\fi}

\newcommand\foreign@monthname{\ifcase\month\or
  January\or February\or March\or April\or May\or June\or
  July\or August\or September\or October\or November\or December\fi}

\newcounter{keywords}
\newcommand\keyword[1]{%
  \global\@namedef{ONKeyword:\expandafter\the\c@keywords}{#1}
  \global\addtocounter{keywords}{1}
}

\renewcommand\frontmatter{%
  \cleardoublepage
  \@mainmatterfalse
  \pagenumbering{roman}
  \makecoverpage
  \ifthenelse{\boolean{maledoc}}{\blankpage}{\makecatalog}%
  \makefrontpage
  \setcounter{page}{5}
  \pagestyle{plain}
}

\renewcommand\mainmatter{%
  \on@mainBegin
  \cleardoublepage
  \@mainmattertrue
  \pagestyle{headings}
  \pagenumbering{arabic}}

\renewcommand\backmatter{%
  \if@openright
    \cleardoublepage
  \else
    \clearpage
  \fi}

\renewcommand\maketitle{%
  \pagestyle{empty}
  \ltx@ifpackageloaded{hyperref}{\on@hypersetup}{}%
  \begin{titlepage}
  \begin{center}
  \vspace*{1.5mm}
  \setlength\baselineskip{0pt}
  \setlength\parskip{1mm}
  \makebox[5cm][c]{\includegraphics[height=5.0cm]{on}}
  \end{center}
  \vspace{1.05cm}
  \begin{center}
  \nohyphens{\MakeUppercase{\local@doctype\ de \@degreename}}\par
	  \vspace*{3cm}
  \nohyphens{\MakeUppercase\local@title}\par
  \vspace*{3cm}
	  \nohyphens{\MakeUppercase{\@authname\ \@authsurn}}\par
  \vspace*{\fill}
  \MakeUppercase\local@cityname\par
  \number\year
  \end{center}
  \end{titlepage}
  \global\let\maketitle\relax%
  \global\let\and\relax}

\newcommand\makecoverpage{%
  \thispagestyle{empty}
  \begin{center}
  \vspace*{1.5mm}
  \setlength\baselineskip{20pt}
  \setlength\parskip{0mm}
  \nohyphens{\local@universityname}\par
  \nohyphens{\local@institutename}\par
  \nohyphens{Programa de P{\' o}s-Gradua{\c c}{\~ a}o}\par
  \vspace{1cm}
  \nohyphens{\local@doctype\ de \@degreename}\par
  \vspace{1cm}
  \nohyphens{\MakeUppercase\local@title}\par
  \vspace*{0.8cm}
  por\par
  \vspace*{0.8cm}
  \nohyphens{\@authname\ \@authsurn}\par
  \end{center}
  \vspace*{1.6cm}
  \begin{flushright}
  \begin{minipage}{8.45cm}
  \frontcover@maintext
  \end{minipage}\par
  \vspace*{7.5mm}
  \nohyphens{%
  \begin{tabularx}{8.45cm}[b]{@{}l@{ }>{\raggedright\arraybackslash}X@{}}
    \local@advisorstring: & \@advtitle\ \@advname\ \@advsurn
        \vspace*{5.0mm} \\
    \ifnum\@coadvisor=0
    \else
    \local@coadvisorstring: &
    \fi
    \count1=0
    \toks@={}
    \@whilenum \count1<\@coadvisor \do{%
    \ifcase\count1 % same as \ifnum0=\count1
      \toks@=\expandafter{\csname ONcoAdvisorTitle:\the\count1%
        \expandafter\endcsname\expandafter\space%
        \csname ONcoAdvisorName:\the\count1%
        \expandafter\endcsname\expandafter\space%
        \csname ONcoAdvisorSurname:\the\count1\endcsname\\}
    \else
      \toks@=\expandafter\expandafter\expandafter{%
        \expandafter\the\expandafter\toks@%
        \expandafter&\expandafter\space%
        \csname ONcoAdvisorTitle:\the\count1\expandafter\endcsname%
        \expandafter\space\csname ONcoAdvisorName:\the\count1\expandafter\endcsname
        \expandafter\space\csname ONcoAdvisorSurname:\the\count1\endcsname\\
      }%
    \fi
    \advance\count1 by 1}
    \the\toks@
  \end{tabularx}}\par
  \end{flushright}
  \vspace*{\fill}
  \begin{center}
  \local@cityname, \local@statename\ -- \local@countryname\par
  \local@monthname\ de \number\year
  \end{center}
  \clearpage
}

\newcommand\makefrontpage{%
  \thispagestyle{empty}
  \begin{center}
    ``\sloppy\nohyphens{\MakeUppercase\local@title}''\par
    \vspace*{7mm}
    {\MakeUppercase\@authname\ \MakeUppercase\@authsurn}\par
  \end{center}\par
  \vspace*{4mm}
  \frontpage@maintext
  \vspace*{8mm}
  \noindent\local@approvedname:\par
  \begin{flushright}
            \vskip16\p@ \baselineskip12pt
        \parbox{10cm}{\hrulefill}\\
        \parbox{9.9cm}{%
                  \raggedright\baselineskip12pt\nohyphens{%
                  \@advtitle\ \@advname\ \@advsurn\ -- \@advinst\hfill}}\\
        \parbox{9.9cm}{(\local@advisorstring)\hfill}\\
        \count1=0
        \@whilenum \count1<\@coadvisor \do {
            \vskip26\p@ \baselineskip12pt
        \parbox{10cm}{\hrulefill}\\
        \parbox{9.9cm}{%
                  \raggedright\baselineskip12pt\nohyphens{%
                  \csname ONcoAdvisorTitle:\the\count1%
                  \endcsname\expandafter\space%
                  \csname ONcoAdvisorName:\the\count1%
                  \endcsname\expandafter\space%
                  \csname ONcoAdvisorSurname:\the\count1%
                  \endcsname\expandafter\space -- %
                  \csname ONcoAdvisorInst:\the\count1 \endcsname\hfill}}\\
        \parbox{9.9cm}{(Co-orientador)\hfill} \\
            \advance\count1 by 1}
        \count1=0
        \@whilenum \count1<\@examiner \do {
            \vskip26\p@ \baselineskip12pt
        \parbox{10cm}{\hrulefill}\\
        \parbox{9.9cm}{%
                  \raggedright\baselineskip12pt\nohyphens{%
                  \csname ONExaminerName:\the\count1% 
                  \endcsname\expandafter\space -- %
                  \csname ONExaminerInst:\the\count1 \endcsname\hfill}}\\
            \advance\count1 by 1}
  \end{flushright}
  \vspace*{\fill}
  \frontpage@bottomtext
  \blankpage}

\newcommand\on@hypersetup{%
\begingroup
  % changes to \toks@ and \count@ are kept local;
  % it's not necessary for them, but it is usually the case
  % for \count1, because the first ten counters are written
  % to the DVI file, thus you got lucky because of PDF output
  \toks@={}% in this special case not necessary
  \count@=0 %
  \@whilenum\count@<\value{keywords}\do{%
    % * a keyword separator is not necessary,
    %    if there is just one keyword
    % * \csname ONKeyword:\the\count@\endcsname must be expanded
    %    at least once, to get rid of the loop depended \count@
    \ifcase\count@ % same as \ifnum0=\count@
      \toks@=\expandafter{\csname ONKeyword:\the\count@\endcsname}%
    \else
      \toks@=\expandafter\expandafter\expandafter{%
        \expandafter\the\expandafter\toks@
        \expandafter;\expandafter\space
        \csname ONKeyword:\the\count@\endcsname
      }%
    \fi
    \advance\count@ by 1 %
  }%
  \edef\x{\endgroup
    \noexpand\hypersetup{%
      pdfkeywords={\the\toks@}%
    }%
  }%
\x
\hypersetup{%
  pdfauthor={\@authname\ \@authsurn},
  pdftitle={\local@title},
  pdfsubject={\local@doctype\ de \@degreename\ em \local@deptname\ do ON/MCTIC},
  pdfcreator={LaTeX with ONTeX toolkit},
  breaklinks={true},
  raiselinks={true},
  pageanchor={true},
  pdfborder={0 0 0},
  pdfborderstyle={},
}}

\newcommand\makecatalog{%
  \thispagestyle{empty}
  \vspace*{\fill}
  \begin{center}
    \setlength{\fboxsep}{5mm}
    \framebox[145mm][c]{%
      \begin{minipage}[t]{15mm}
      \noindent\nohyphens\@lcutter\@ncutter\hfill
      \end{minipage}\makebox[5mm][c]{}%
      \begin{minipage}[t]{115mm}
      \setlength\baselineskip{14pt}
      \setlength\parskip{0mm}
      \renewcommand{\arraystretch}{0.7}
      \setlength{\parindent}{1.2em}
      \noindent\sloppy\nohyphens\@authsurn,
      \nohyphens\@authname\par
      \raggedright\setlength{\parindent}{1.2em}
      \nohyphens{\local@title\ 
%      / \@authname\ \@authsurn. -- 
      [\local@cityname] \number\year.}\par
      \pageref{front:pageno}, \pageref{LastPage} p.\ 29,7 cm: 
      \@ifundefined{r@cat:lofflag}{}{\pageref{cat:lofflag}}
      \@ifundefined{r@cat:lotflag}{}{\pageref{cat:lotflag}}
      \setlength\parskip{10mm}\par
      \raggedright\setlength{\parindent}{1.2em}
      \nohyphens{\local@doctype\ ({\MakeLowercase\@degreename}) -
      \local@institutename\ -
%     ,\ Programa de P{\' o}s-gradua{\c c}{\~ a}o em \local@deptname,
      \local@cityname, \number\year.}
      \setlength\parskip{5mm}\par
%      \nohyphens{%
%      \begin{tabularx}{100mm}[b]{@{}l@{ }>{\raggedright\arraybackslash}X@{}}
%        \local@advisorstring: & \@advname\ \@advsurn \\
%        \ifnum\@coadvisor=0
%        \else
%        \local@coadvisorstring: &
%        \fi
%        \count1=0
%        \toks@={}
%        \@whilenum \count1<\@coadvisor \do{%
%        \ifcase\count1 % same as \ifnum0=\count1
%          \toks@=\expandafter{\csname ONcoAdvisorName:\the\count1%
%          \expandafter\endcsname\expandafter\space%
%          \csname ONcoAdvisorSurname:\the\count1\endcsname\\}
%        \else
%          \toks@=\expandafter\expandafter\expandafter{%
%            \expandafter\the\expandafter\toks@
%            \expandafter&\expandafter\space
%            \csname ONcoAdvisorName:\the\count1\expandafter\endcsname%
%            \expandafter\space\csname ONcoAdvisorSurname:\the\count1\endcsname\\
%          }%
%        \fi
%        \advance\count1 by 1}
%        \the\toks@
%      \end{tabularx}}\par\ \par
%      \bibname: p. \pageref{bib:begin} -- \pageref{bib:end}.\par\ \par
      \count1=0
      \count2=1
      \raggedright\setlength{\parindent}{1.2em}
      \nohyphens{\@whilenum \count1<\value{keywords} \do {%
        \number\count2. \csname ONKeyword:\the\count1 \endcsname.
        \advance\count1 by 1
        \advance\count2 by 1}
%      I. \@advsurn, \@advname 
%      \ifthenelse{\@coadvisor>0}{\ \emph{et~al.}{.}}.
%      II. \local@institutename, Programa de P{\' o}s-gradua{\c c}{\~ a}o
%      em \local@deptname.
%      III. T{\' i}tulo.}
      I. \local@institutename.
      II. T{\' i}tulo.}\par
      \raggedleft CDU \@ncdu
    \end{minipage}}
  \end{center}
%  \vspace*{\fill}
  \clearpage
}

\newcommand\dedication[1]{
  \gdef\@dedic{#1}
    \cleardoublepage
    \pagestyle{plain}
    \vspace*{\fill}
    \begin{flushright}
      \begin{minipage}{60mm}
        \raggedleft \it \normalsize \@dedic
      \end{minipage}
    \end{flushright}}

\newenvironment{abstract}{%
  \cleardoublepage
%  \abstract@toptext\par
%  \vspace*{8.6mm}
  \begin{center}
    \@authname\ \@authsurn \par
    \vspace*{7mm}
    \sloppy\nohyphens{\MakeUppercase\local@title}\par
    \vspace*{7mm}
%    \local@monthname/\number\year\par
    \MakeUppercase{\textbf{\large RESUMO}}\par
    \vspace*{4mm}
  \end{center}\par
%  \vspace*{\fill}
%  \noindent%
%  \begin{tabularx}{\textwidth}[b]{@{}l@{ }>{\raggedright\arraybackslash}X@{}}
%      \local@advisorstring: & \@advname\ \@advsurn
%        \vspace*{5.0mm} \\
%    \ifnum\@coadvisor=0
%    \else
%    \local@coadvisorstring: &
%    \fi
%    \count1=0
%    \toks@={}
%    \@whilenum \count1<\@coadvisor \do{%
%    \ifcase\count1 % same as \ifnum0=\count1
%      \toks@=\expandafter{\csname ONcoAdvisorName:\the\count1%
%      \expandafter\endcsname\expandafter\space%
%      \csname ONcoAdvisorSurname:\the\count1\endcsname\\}
%    \else
%      \toks@=\expandafter\expandafter\expandafter{%
%        \expandafter\the\expandafter\toks@
%        \expandafter&\expandafter\space
%        \csname ONcoAdvisorName:\the\count1\expandafter\endcsname%
%        \expandafter\space\csname ONcoAdvisorSurname:\the\count1\endcsname\\
%      }%
%    \fi
%    \advance\count1 by 1}
%    \the\toks@
%  \end{tabularx}\par
%  \vspace*{2mm}
%  \noindent\local@deptstring: \local@deptname\par
%  \vspace*{7mm}
}{\vspace*{\fill}}

\newenvironment{foreignabstract}{%
  \cleardoublepage
  \begin{otherlanguage}{english}
%  \foreignabstract@toptext\par
%  \vspace*{8.6mm}
  \begin{center}
    \@authname\ \@authsurn \par
    \vspace*{7mm}
    \sloppy\nohyphens{\MakeUppercase\foreign@title}\par
    \vspace*{7mm}
%    \foreign@monthname/\number\year
    \MakeUppercase{\textbf{\large ABSTRACT}}\par
    \vspace*{4mm}
  \end{center}\par
%  \vspace*{\fill}
%  \noindent%
%  \begin{tabularx}{\textwidth}[b]{@{}l@{ }>{\raggedright\arraybackslash}X@{}}
%    \foreign@advisorstring: & \@advname\ \@advsurn
%        \vspace*{5.0mm} \\
%    \ifnum\@coadvisor=0
%    \else
%    \foreign@coadvisorstring: &
%    \fi
%    \count1=0
%    \toks@={}
%    \@whilenum \count1<\@coadvisor \do{%
%    \ifcase\count1 % same as \ifnum0=\count1
%      \toks@=\expandafter{\csname ONcoAdvisorName:\the\count1%
%      \expandafter\endcsname\expandafter\space%
%      \csname ONcoAdvisorSurname:\the\count1\endcsname\\}
%    \else
%      \toks@=\expandafter\expandafter\expandafter{%
%        \expandafter\the\expandafter\toks@
%        \expandafter&\expandafter\space
%        \csname ONcoAdvisorName:\the\count1\expandafter\endcsname%
%        \expandafter\space\csname ONcoAdvisorSurname:\the\count1\endcsname\\
%      }%
%    \fi
%    \advance\count1 by 1}
%    \the\toks@
%  \end{tabularx}\par
%  \vspace*{2mm}
%  \noindent\foreign@deptstring: \foreign@deptname\par
%  \vspace*{7mm}
  }{%
  \end{otherlanguage}
  \vspace*{\fill}
  \global\let\@author\@empty
  \global\let\@date\@empty
  \global\let\foreign@title\@empty
  \global\let\foreign@title\relax
  \global\let\local@title\@empty
  \global\let\local@title\relax
  \global\let\author\relax
  \global\let\author\relax
  \global\let\date\relax}

\renewcommand\listoffigures{%
    \if@twocolumn
      \@restonecoltrue\onecolumn
    \else
      \@restonecolfalse
    \fi
    \chapter*{\LARGE \listfigurename}%
    \on@hasLof
      \addcontentsline{toc}{chapter}{\listfigurename}%
      \@mkboth{\MakeUppercase\listfigurename}%
              {\MakeUppercase\listfigurename}%
    \@starttoc{lof}%
    \if@restonecol\twocolumn\fi
    }

\renewcommand\listoftables{%
    \if@twocolumn
      \@restonecoltrue\onecolumn
    \else
      \@restonecolfalse
    \fi
    \chapter*{\LARGE \listtablename}%
      \on@hasLot
      \addcontentsline{toc}{chapter}{\listtablename}%
      \@mkboth{%
          \MakeUppercase\listtablename}%
         {\MakeUppercase\listtablename}%
    \@starttoc{lot}%
    \if@restonecol\twocolumn\fi
    }

\renewcommand\tableofcontents{%
    \if@twocolumn
      \@restonecoltrue\onecolumn
    \else
      \@restonecolfalse
    \fi
    \chapter*{\LARGE \contentsname
        \@mkboth{%
           \MakeUppercase\contentsname}{\MakeUppercase\contentsname}}%
    \@starttoc{toc}%
    \if@restonecol\twocolumn\fi
    }

\newcommand\printlosymbols{%
\renewcommand\glossaryname{\listsymbolname}%
\@input@{\jobname.los}}
\def\makelosymbols{%
  \newwrite\@losfile
  \immediate\openout\@losfile=\jobname.syx
  \def\symbl{\@bsphack\begingroup
             \@sanitize
             \@wrlos}\typeout
  {Writing index of symbols file \jobname.syx}%
  \let\makelosymbols\@empty
}
\@onlypreamble\makelosymbols
\AtBeginDocument{%
\@ifpackageloaded{hyperref}{%
  \def\@wrlos#1#2{%
    \protected@write\@losfile{}%
      {\string\indexentry{[#1] #2|hyperpage}{\thepage}}%
    \endgroup
    \@esphack}}{%
  \def\@wrlos#1#2{%
    \protected@write\@losfile{}%
      {\string\indexentry{[#1] #2}{\thepage}}%
    \endgroup
    \@esphack}}}

\newcommand\printloabbreviations{%
\renewcommand\glossaryname{\listabbreviationname}%
\@input@{\jobname.lab}}
\def\makeloabbreviations{%
  \newwrite\@labfile
  \immediate\openout\@labfile=\jobname.abx
  \def\abbrev{\@bsphack\begingroup
              \@sanitize
              \@wrlab}\typeout
  {Writing index of abbreviations file \jobname.abx}%
  \let\makeloabbreviations\@empty
}
\@onlypreamble\makeloabbreviations
\AtBeginDocument{%
\@ifpackageloaded{hyperref}{%
  \def\@wrlab#1#2{%
    \protected@write\@labfile{}%
      {\string\indexentry{[#1] #2|hyperpage}{\thepage}}%
    \endgroup
    \@esphack}}{%
  \def\@wrlab#1#2{%
    \protected@write\@labfile{}%
      {\string\indexentry{[#1] #2}{\arabic{page}}}%
    \endgroup
    \@esphack}}}
\AtBeginDocument{%
  \ltx@ifpackageloaded{hyperref}{
    \def\on@bibEnd{%
      \immediate\write\@auxout{%
        \string\newlabel{bib:end}{{}{\arabic{page}}{}{page.\arabic{page}}{}}}}%
    \def\on@bibBegin{%
      \immediate\write\@auxout{%
        \string\newlabel{bib:begin}{{}{\arabic{page}}{}{page.\arabic{page}}{}}}}%
    \def\on@mainBegin{%
      \immediate\write\@auxout{%
        \string\newlabel{front:pageno}{{}{\roman{page}}{}{page.\roman{page}}{}}}}%
    \def\on@hasLof{%
      \immediate\write\@auxout{%
        \string\newlabel{cat:lofflag}{{}{graf.~il.}{}{page.\roman{page}}{}}}}%
    \def\on@hasLot{%
      \immediate\write\@auxout{%
	      \string\newlabel{cat:lotflag}{{}{tab.}{}{page.\roman{page}}{}}}}%
  }{%
    \def\on@bibEnd{%
      \immediate\write\@auxout{%
      \string\newlabel{bib:end}{{}{\arabic{page}}{}}}}%
    \def\on@bibBegin{%
      \immediate\write\@auxout{%
      \string\newlabel{bib:begin}{{}{\arabic{page}}{}}}}%
    \def\on@mainBegin{%
      \immediate\write\@auxout{%
        \string\newlabel{front:pageno}{{}{\roman{page}}{}}}}%
    \def\on@hasLof{%
      \immediate\write\@auxout{%
        \string\newlabel{cat:lofflag}{{}{graf.~il.}{}}}}%
    \def\on@hasLot{%
      \immediate\write\@auxout{%
        \string\newlabel{cat:lotflag}{{}{tab.}{}}}}%
  }%
}

\renewcommand\@biblabel[1]{} % to avoid the leading number in bib list
\newdimen\bibindent%
\setlength\bibindent{1.5em}%
\renewenvironment{thebibliography}[1]%
     {\onehalfspacing%
      \chapter*{\LARGE \bibname}%
      \on@bibBegin
      \addcontentsline{toc}{chapter}{\bibname}%
      \@mkboth{%
          \MakeUppercase\bibname}%
         {\MakeUppercase\bibname}%
      \list{\@biblabel{\@arabic\c@enumiv}}%
           {\setlength{\labelwidth}{0ex}%
            \setlength{\leftmargin}{9.0ex}%
            \setlength{\itemindent}{-9.0ex}%
            \advance\leftmargin\labelsep%
            \@openbib@code%
            \usecounter{enumiv}%
            \let\p@enumiv\@empty%
            \renewcommand\theenumiv{\@arabic\c@enumiv}}%
      \sloppy%
      \clubpenalty4000%
      \@clubpenalty \clubpenalty%
      \widowpenalty4000%
      \sfcode`\.\@m}%
     {\def\@noitemerr%
       {\@latex@warning{Empty `thebibliography' environment}}%
      \endlist\on@bibEnd}

\newenvironment{theglossary}{%
  \if@twocolumn%
    \@restonecoltrue\onecolumn%
  \else%
    \@restonecolfalse%
  \fi%
  \@mkboth{\MakeUppercase\glossaryname}%
  {\MakeUppercase\glossaryname}%
  \chapter*{\LARGE \glossaryname}%
  \addcontentsline{toc}{chapter}{\glossaryname}
  \list{}
  {\setlength{\listparindent}{0in}%
   \setlength{\labelwidth}{1.0in}%
   \setlength{\leftmargin}{1.5in}%
   \setlength{\labelsep}{0.5in}%
   \setlength{\itemindent}{0in}}%
   \sloppy}%
  {\if@restonecol\twocolumn\fi%
\endlist}

\renewenvironment{theindex}{%
  \if@twocolumn
    \@restonecolfalse
  \else
    \@restonecoltrue
  \fi
  \twocolumn[\@makeschapterhead{\indexname}]%
  \@mkboth{\MakeUppercase\indexname}%
  {\MakeUppercase\indexname}%
  \thispagestyle{plain}\parindent\z@
  \addcontentsline{toc}{chapter}{\indexname}
  \parskip\z@ \@plus .3\p@\relax
  \columnseprule \z@
  \columnsep 35\p@
  \let\item\@idxitem}
  {\if@restonecol\onecolumn\else\clearpage\fi}

\newcommand\glossaryname{Gloss{\' a}rio}
\newcommand\listabbreviationname{Lista de Abreviaturas}
\newcommand\listsymbolname{Lista de S{\' i}mbolos}
\newcommand\local@advisorstring{Orientador}
\newcommand\foreign@advisorstring{Advisor}
\newcommand\local@coadvisorstring{Co-orientador}
\newcommand\foreign@coadvisorstring{Co-advisor}
\ifthenelse{\boolean{maledoc}}{%
  \newcommand\local@approvedname{Aprovado por}%
}{%
  \newcommand\local@approvedname{Aprovada por}%
}
\newcommand\local@institutename{Observat{\' o}rio Nacional}
\newcommand\local@universityname{Minist{\' e}rio da Ci{\^ e}ncia, Tecnologia, Inova{\c c}{\~ o}es e Comunica{\c c}{\~ o}es}
\newcommand\local@deptstring{Programa}
\newcommand\foreign@deptstring{Graduate Program}
\newcommand\local@cityname{Rio de Janeiro}
\newcommand\local@statename{RJ}
\newcommand\local@countryname{Brasil}

\newcommand\frontcover@maintext{
  \sloppy\nohyphens{\local@doctype\  
  \ifthenelse{\boolean{maledoc}}{apresentado}{submetida}
  ao Corpo Docente do Programa de P{\' o}s-gradua{\c c}{\~ a}o em \local@deptname\ do
  \local@institutename, como parte dos requisitos
  necess{\' a}rios para a obten{\c c}{\~ a}o do \ifthenelse{\boolean{doutboolean}}{Grau}{T{\' i}tulo}
  de \local@degname\ em \local@deptname.}
}

\newcommand\frontpage@maintext{
  \noindent {\MakeUppercase\local@doctype}
  \ifthenelse{\boolean{maledoc}}{APRESENTADO}{SUBMETIDA}
  \sloppy\nohyphens{AO CORPO DOCENTE DO PROGRAMA DE P{\' O}S-GRADUA{\c C}{\~ A}O EM
  {\MakeUppercase\local@deptname} DO OBSERVAT{\' O}RIO
  NACIONAL COMO PARTE DOS REQUISITOS
  NECESS{\' A}RIOS PARA A OBTEN{\c C}{\~ A}O DO
  \ifthenelse{\boolean{doutboolean}}{GRAU}{T{\' I}TULO} DE
  {\MakeUppercase\local@degname} EM
  {\MakeUppercase\local@deptname.\par}}%
}

\newcommand\frontpage@bottomtext{%
  \begin{center}
  {\MakeUppercase{\local@cityname, \local@statename\ -- \local@countryname}}\par
  {\number\day\ DE \MakeUppercase\local@monthname\ DE \number\year}
  \end{center}
}

\newcommand\abstract@toptext{%
  \noindent Resumo \ifthenelse{\boolean{maledoc}}{do}{da}
  \local@doctype\ \ifthenelse{\boolean{maledoc}}{apresentado}{apresentada}
  \sloppy\nohyphens{ao Programa de P{\' o}s-gradua{\c c}{\~ a}o em \local@deptname\ do Observat{\' o}rio Nacional/MCTIC como parte dos requisitos
  necess{\' a}rios para a obten{\c c}{\~ a}o do
  \ifthenelse{\boolean{doutboolean}}{grau}{t{\' i}tulo} de
  \local@degname\ em \local@deptname\ (\@degree)}
}

\newcommand\foreignabstract@toptext{%
  \noindent \sloppy\nohyphens{Abstract of the \foreign@doctype\ presented to the
  Observat{\' o}rio Nacional/MCTIC as a partial fulfillment of the requirements for the
  degree of \foreign@degname\ in \foreign@deptname\ (\foreign@degree)}
}

%
%  These Macros are taken from the AAS TeX macro package version 5.2
%  Needed to resolve the macro definitions in the TeX/BibTeX entries returned by
%  the ADS abstract service.

\let\jnl@style=\rm
\def\ref@jnl#1{{\jnl@style#1}}

\def\actaa{\ref@jnl{Acta Astron.}}                % Acta Astronomica
\def\araa{\ref@jnl{Ann. Rev. Astron. Astrohys.}}  % Annual Review of Astron and Astrophys
\def\ao{\ref@jnl{Appl. Optics}}                   % Applied Optics
\def\aspc{\ref@jnl{ASP Conf. Ser.}}               % ASP Conference Series
\def\afz{\ref@jnl{Astrofizika}}                   % Astrofizika
\def\aj{\ref@jnl{Astron. J.}}                     % Astronomical Journal
\def\azh{\ref@jnl{Astron. Zh.}}                   % Astronomicheskii Zhurnal
\def\aap{\ref@jnl{Astron. Astrophys.}}            % Astronomy and Astrophysics
\def\aapr{\ref@jnl{Astron. Astrophys. Rev.}}      % Astronomy and Astrophysics Reviews
\def\aaps{\ref@jnl{Astron. Astrophys. Suppl.}}    % Astronomy and Astrophysics, Supplement
\def\arep{\ref@jnl{Astron. Rep.}}                 % Astronomy Reports
\def\apj{\ref@jnl{Astrophys. J.}}                 % Astrophysical Journal
\def\apjl{\ref@jnl{Astrophys. J. Lett.}}          % Astrophysical Journal, Letters
\def\apjs{\ref@jnl{Astrophys. J. Suppl.}}         % Astrophysical Journal, Supplement
\def\aplett{\ref@jnl{Astrophys. Lett.}}           % Astrophysics Letters
\def\apspr{\ref@jnl{Astrophys. Space Phys. Res.}} % Astrophysics Space Physics Research
\def\apss{\ref@jnl{Astrophys. Space Sci.}}        % Astrophysics and Space Science
\def\baas{\ref@jnl{Bull. AAS}}                    % Bulletin of the AAS
\def\bac{\ref@jnl{Bull. Astron. Inst. Czechoslovakia}}  % Bulletin of the Astronomical Institutes of Czechoslovakia 
\def\bain{\ref@jnl{Bull. Astron. Inst. Netherlands}}    % Bulletin Astronomical Institute of the Netherlands
\def\caa{\ref@jnl{Chinese Astron. Astrophys.}}    % Chinese Astronomy and Astrophysics
\def\cjaa{\ref@jnl{Chinese J. Astron. Astrophys.}}% Chinese Journal of Astronomy and Astrophysics
\def\fcp{\ref@jnl{Fund. Cosmic Phys.}}            % Fundamental Cosmic Physics
\def\gca{\ref@jnl{Geochim. Cosmochim. Acta}}      % Geochimica Cosmochimica Acta
\def\grl{\ref@jnl{Geophys. Res. Lett.}}           % Geophysics Research Letters
\def\iaucirc{\ref@jnl{IAU~Circ.}}                 % IAU Cirulars
\def\icarus{\ref@jnl{Icarus}}                     % Icarus
\def\japa{\ref@jnl{J. Astrophys. Astron.}}        % Journal of Astrophysics and Astronomy
\def\jcp{\ref@jnl{J. Chem. Phys.}}                % Journal of Chemical Physics
\def\jcap{\ref@jnl{J. Cosmology Astropart. Phys.}}% Journal of Cosmology and Astroparticle Physics
\def\jgr{\ref@jnl{J. Geophys. Res.}}              % Journal of Geophysics Research
\def\jqsrt{\ref@jnl{J. Quant. Spec. Radiat. Transf.}}  % Journal of Quantitiative Spectroscopy and Radiative Transfer
\def\jrasc{\ref@jnl{J. Roy. Astron. Soc. Canada}} % Journal of the RAS of Canada
\def\memras{\ref@jnl{Mem. Roy. Astron. Soc.}}     % Memoirs of the RAS
\def\memsai{\ref@jnl{Mem. Soc. Astron. Italiana}} % Memorie Societa Astronomica Italiana
\def\mnassa{\ref@jnl{Mon. Not. Astron. Soc. S. Africa}}  % Monthly Notes of the Astronomical Society of Southern Africa
\def\mnras{\ref@jnl{Mon. Not, Roy. Astron. Soc.}} % Monthly Notices of the RAS
\def\nat{\ref@jnl{Nature}}                        % Nature
\def\na{\ref@jnl{New Astron.}}                    % New Astronomy
\def\nar{\ref@jnl{New Astron. Rev.}}              % New Astronomy Review
\def\nphysa{\ref@jnl{Nucl. Phys. A}}              % Nuclear Physics A
\def\physscr{\ref@jnl{Phys. Scripta}}                 % Physica Scripta
\def\pra{\ref@jnl{Phys. Rev. A}}                  % Physical Review A: General Physics
\def\prb{\ref@jnl{Phys. Rev. B}}                  % Physical Review B: Solid State
\def\prc{\ref@jnl{Phys. Rev. C}}                  % Physical Review C
\def\prd{\ref@jnl{Phys. Rev. D}}                  % Physical Review D
\def\pre{\ref@jnl{Phys. Rev. E}}                  % Physical Review E
\def\prl{\ref@jnl{Phys. Rev. Lett.}}              % Physical Review Letters
\def\physrep{\ref@jnl{Phys. Rep.}}                % Physics Reports
\def\planss{\ref@jnl{Planet. Space Sci.}}         % Planetary Space Science
\def\procspie{\ref@jnl{Proc. SPIE}}               % Proceedings of the SPIE
\def\pasa{\ref@jnl{Publ. Astron. Soc. Australia}} % Publications of the Astron. Soc. of Australia
\def\pasj{\ref@jnl{Publ. Astron. Soc. Japan}}     % Publications of the ASJ
\def\pasp{\ref@jnl{Publ. Astron. Soc. Pacific}}   % Publications of the ASP
\def\qjras{\ref@jnl{Quart. J. Roy. Astron. Soc.}} % Quarterly Journal of the RAS
\def\rmxaa{\ref@jnl{Rev. Mex. Astron. Astrofis.}} % Revista Mexicana de Astronomia y Astrofisica
\def\sci{\ref@jnl{Science}}                       % Science
\def\skytel{\ref@jnl{Sky \& Telesc.}}             % Sky and Telescope
\def\solphys{\ref@jnl{Sol. Phys.}}                % Solar Physics
\def\sovast{\ref@jnl{Soviet Astron.}}             % Soviet Astronomy
\def\ssr{\ref@jnl{Space Sci. Rev.}}               % Space Science Reviews
\def\zap{\ref@jnl{Z. Astrophys.}}                 % Zeitschrift fuer Astrophysik

\let\astap=\aap
\let\apjlett=\apjl
\let\apjsupp=\apjs
\let\applopt=\ao

% Astronomy and Astrophysics symbol macros

\newcommand\getsto{\mathrel{\mathchoice {\vcenter{\offinterlineskip
\halign{\hfil
$\reset@font\displaystyle##$\hfil\cr\gets\cr\to\cr}}}
{\vcenter{\offinterlineskip\halign{\hfil$\reset@font\textstyle##$\hfil\cr\gets
\cr\to\cr}}}
{\vcenter{\offinterlineskip\halign{\hfil$\reset@font\scriptstyle##$\hfil\cr\gets
\cr\to\cr}}}
{\vcenter{\offinterlineskip\halign{\hfil$\reset@font\scriptscriptstyle##$\hfil\cr
\gets\cr\to\cr}}}}}

\newcommand\cor{\mathrel{\mathchoice {\hbox{$\widehat=$}}{\hbox{$\widehat=$}}
{\hbox{$\reset@font\scriptstyle\hat=$}}
{\hbox{$\reset@font\scriptscriptstyle\hat=$}}}}

\newcommand\lid{\mathrel{\mathchoice {\vcenter{\offinterlineskip\halign{\hfil
$\reset@font\displaystyle##$\hfil\cr<\cr\noalign{\vskip1.2pt}=\cr}}}
{\vcenter{\offinterlineskip\halign{\hfil$\reset@font\textstyle##$\hfil\cr<\cr
\noalign{\vskip1.2pt}=\cr}}}
{\vcenter{\offinterlineskip\halign{\hfil$\reset@font\scriptstyle##$\hfil\cr<\cr
\noalign{\vskip1pt}=\cr}}}
{\vcenter{\offinterlineskip\halign{\hfil$\reset@font\scriptscriptstyle##$\hfil\cr
<\cr
\noalign{\vskip0.9pt}=\cr}}}}}

\newcommand\gid{\mathrel{\mathchoice {\vcenter{\offinterlineskip\halign{\hfil
$\reset@font\displaystyle##$\hfil\cr>\cr\noalign{\vskip1.2pt}=\cr}}}
{\vcenter{\offinterlineskip\halign{\hfil$\reset@font\textstyle##$\hfil\cr>\cr
\noalign{\vskip1.2pt}=\cr}}}
{\vcenter{\offinterlineskip\halign{\hfil$\reset@font\scriptstyle##$\hfil\cr>\cr
\noalign{\vskip1pt}=\cr}}}
{\vcenter{\offinterlineskip\halign{\hfil$\reset@font\scriptscriptstyle##$\hfil\cr
>\cr
\noalign{\vskip0.9pt}=\cr}}}}}

\newcommand\sol{\mathrel{\mathchoice {\vcenter{\offinterlineskip\halign{\hfil
$\reset@font\displaystyle##$\hfil\cr\sim\cr<\cr}}}
{\vcenter{\offinterlineskip\halign{\hfil$\reset@font\textstyle##$\hfil\cr\sim\cr
<\cr}}}
{\vcenter{\offinterlineskip\halign{\hfil$\reset@font\scriptstyle##$\hfil\cr\sim\cr
<\cr}}}
{\vcenter{\offinterlineskip\halign{\hfil$\reset@font\scriptscriptstyle##$\hfil\cr
\sim\cr<\cr}}}}}

\newcommand\sog{\mathrel{\mathchoice {\vcenter{\offinterlineskip\halign{\hfil
$\reset@font\displaystyle##$\hfil\cr\sim\cr>\cr}}}
{\vcenter{\offinterlineskip\halign{\hfil$\reset@font\textstyle##$\hfil\cr\sim\cr
>\cr}}}
{\vcenter{\offinterlineskip\halign{\hfil$\reset@font\scriptstyle##$\hfil\cr
\sim\cr>\cr}}}
{\vcenter{\offinterlineskip\halign{\hfil$\reset@font\scriptscriptstyle##$\hfil\cr
\sim\cr>\cr}}}}}

\newcommand\lse{\mathrel{\mathchoice {\vcenter{\offinterlineskip\halign{\hfil
$\reset@font\displaystyle##$\hfil\cr<\cr\simeq\cr}}}
{\vcenter{\offinterlineskip\halign{\hfil$\reset@font\textstyle##$\hfil\cr
<\cr\simeq\cr}}}
{\vcenter{\offinterlineskip\halign{\hfil$\reset@font\scriptstyle##$\hfil\cr
<\cr\simeq\cr}}}
{\vcenter{\offinterlineskip\halign{\hfil$\reset@font\scriptscriptstyle##$\hfil\cr
<\cr\simeq\cr}}}}}

\newcommand\gse{\mathrel{\mathchoice {\vcenter{\offinterlineskip\halign{\hfil
$\reset@font\displaystyle##$\hfil\cr>\cr\simeq\cr}}}
{\vcenter{\offinterlineskip\halign{\hfil$\reset@font\textstyle##$\hfil\cr
>\cr\simeq\cr}}}
{\vcenter{\offinterlineskip\halign{\hfil$\reset@font\scriptstyle##$\hfil\cr
>\cr\simeq\cr}}}
{\vcenter{\offinterlineskip\halign{\hfil$\reset@font\scriptscriptstyle##$\hfil\cr
>\cr\simeq\cr}}}}}

\newcommand\grole{\mathrel{\mathchoice {\vcenter{\offinterlineskip\halign{\hfil
$\reset@font\displaystyle##$\hfil\cr>\cr\noalign{\vskip-1.5pt}<\cr}}}
{\vcenter{\offinterlineskip\halign{\hfil$\reset@font\textstyle##$\hfil\cr
>\cr\noalign{\vskip-1.5pt}<\cr}}}
{\vcenter{\offinterlineskip\halign{\hfil$\reset@font\scriptstyle##$\hfil\cr
>\cr\noalign{\vskip-1pt}<\cr}}}
{\vcenter{\offinterlineskip\halign{\hfil$\reset@font\scriptscriptstyle##$\hfil\cr
>\cr\noalign{\vskip-0.5pt}<\cr}}}}}

\newcommand\leogr{\mathrel{\mathchoice {\vcenter{\offinterlineskip\halign{\hfil
$\reset@font\displaystyle##$\hfil\cr<\cr\noalign{\vskip-1.5pt}>\cr}}}
{\vcenter{\offinterlineskip\halign{\hfil$\reset@font\textstyle##$\hfil\cr
<\cr\noalign{\vskip-1.5pt}>\cr}}}
{\vcenter{\offinterlineskip\halign{\hfil$\reset@font\scriptstyle##$\hfil\cr
<\cr\noalign{\vskip-1pt}>\cr}}}
{\vcenter{\offinterlineskip\halign{\hfil$\reset@font\scriptscriptstyle##$\hfil\cr
<\cr\noalign{\vskip-0.5pt}>\cr}}}}}

\newcommand\loa{\mathrel{\mathchoice {\vcenter{\offinterlineskip\halign{\hfil
$\reset@font\displaystyle##$\hfil\cr<\cr\approx\cr}}}
{\vcenter{\offinterlineskip\halign{\hfil$\reset@font\textstyle##$\hfil\cr
<\cr\approx\cr}}}
{\vcenter{\offinterlineskip\halign{\hfil$\reset@font\scriptstyle##$\hfil\cr
<\cr\approx\cr}}}
{\vcenter{\offinterlineskip\halign{\hfil$\reset@font\scriptscriptstyle##$\hfil\cr
<\cr\approx\cr}}}}}

\newcommand\goa{\mathrel{\mathchoice {\vcenter{\offinterlineskip\halign{\hfil
$\reset@font\displaystyle##$\hfil\cr>\cr\approx\cr}}}
{\vcenter{\offinterlineskip\halign{\hfil$\reset@font\textstyle##$\hfil\cr
>\cr\approx\cr}}}
{\vcenter{\offinterlineskip\halign{\hfil$\reset@font\scriptstyle##$\hfil\cr
>\cr\approx\cr}}}
{\vcenter{\offinterlineskip\halign{\hfil$\reset@font\scriptscriptstyle##$\hfil\cr
>\cr\approx\cr}}}}}

\newcommand\sun{\hbox{$\odot$}}
\newcommand\earth{\hbox{$\oplus$}}
\newcommand\degr{\hbox{$^\circ$}}
\newcommand\diameter{{\ifmmode\mathchoice
{\ooalign{\hfil\hbox{$\reset@font\displaystyle/$}\hfil\crcr
{\hbox{$\reset@font\displaystyle\mathchar"20D$}}}}
{\ooalign{\hfil\hbox{$\reset@font\textstyle/$}\hfil\crcr
{\hbox{$\reset@font\textstyle\mathchar"20D$}}}}
{\ooalign{\hfil\hbox{$\reset@font\scriptstyle/$}\hfil\crcr
{\hbox{$\reset@font\scriptstyle\mathchar"20D$}}}}
{\ooalign{\hfil\hbox{$\reset@font\scriptscriptstyle/$}\hfil\crcr
{\hbox{$\reset@font\scriptscriptstyle\mathchar"20D$}}}}
\else{\ooalign{\hfil/\hfil\crcr\mathhexbox20D}}%
\fi}}

\newcommand\sq{\hbox{\rlap{$\sqcap$}$\sqcup$}}

\newcommand{\romn}[1] {{\mathrm #1}}

\newcommand\fd{\hbox{$.\!\!^{\reset@font\romn d}$}}
\newcommand\fh{\hbox{$.\!\!^{\reset@font\romn h}$}}
\newcommand\fm{\hbox{$.\!\!^{\reset@font\romn m}$}}
\newcommand\fs{\hbox{$.\!\!^{\reset@font\romn s}$}}
\newcommand\fdg{\hbox{$.\!\!^\circ$}}
\newcommand\farcm{\hbox{$.\mkern-4mu^\prime$}}
\newcommand\farcs{\hbox{$.\!\!^{\prime\prime}$}}
\newcommand\fp{\hbox{$.\!\!^{\reset@font\reset@font\scriptscriptstyle\romn p}$}}
\newcommand\arcmin{\hbox{$^\prime$}}
\newcommand\arcsec{\hbox{$^{\prime\prime}$}}

\newcommand\micron{\hbox{$\umu$m}}
\newcommand\ion[2]{\text{#1\,\textsc{\lowercase{#2}}}}	% ionization states

%%
%%
%% End of file `on.cls'.

