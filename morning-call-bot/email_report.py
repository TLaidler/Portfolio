# Bibliotecas padrão
import datetime as dt
from dateutil.relativedelta import relativedelta
from datetime import timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib

# Bibliotecas de terceiros
from pytz import utc

USER_EMAIL = "ESCREVA AQUI"
PASSWORD = "ESCREVA SENHA GMAIL (APP-PASSWORD)"

hoje = dt.datetime.now(tz=utc) #- relativedelta(days=4) Pode ser util


def send_automatic_email(message, data_posicao, remetentes, fromaddr = f"{USER_EMAIL}"):
    login = f"{USER_EMAIL}"
    password = f"{PASSWORD}"  # mudar
    toaddr = " , ".join(remetentes)

    # instance of MIMEMultipart
    msg = MIMEMultipart()

    # storing the senders email address
    msg['From'] = fromaddr

    # storing the receivers email address
    msg['To'] = toaddr

    # storing the subject
    msg['Subject'] = f" Noticias do dia {data_posicao}"

    # string to store the body of the mail
    body = f''' 
    <p>Prezados,</p>
    <p>Segue o resumo das notícias do dia {data_posicao}:</p>
   
    {message}
    <p>Abraços!</p>
</body>
</html>
'''
    # attach the body with the msg instance
    #msg.attach(MIMEText(body, 'plain'))
    msg.attach(MIMEText(body, 'html'))
    # creates SMTP session
    s = smtplib.SMTP('smtp.gmail.com', 587)

    # start TLS for security
    s.starttls()

    # Authentication
    s.login(fromaddr, f"{PASSWORD}")
    # Converts the Multipart msg into a string
    text = msg.as_string()

    # sending the mail
    s.sendmail(fromaddr, remetentes, text)

    # terminating the session
    s.quit()

def send_news_now(message):
    try:
        send_automatic_email(message, hoje.strftime('%Y-%m-%d'), ['ESCREVA O EMAIL DO REMETENTE'])
        print("Email enviado!")
        return True
    except:
        print("Email não foi enviado com sucesso")
        return False
