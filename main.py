import telebot
from lagrange import lagrange
import numpy as np
import base64
from PIL import Image
import io
from random import seed

with open("pic.jpg", "rb") as img_file:
    my_string = base64.b16encode(img_file.read())

print(len(my_string))

str_list = [my_string[i:i + 4] for i in range(0, len(my_string), 4)]
int_list = [int(x, 16) for x in str_list]
M = len(int_list)
bot = telebot.TeleBot('1028836186:AAGc-g3It4EojXWSGW6ZmIzX8eZqwG6uOWI')

n = 5
k = 2
P = 65581

polynomial_coeffs = np.random.randint(P, size=(M, k))
users_list = []

xs_received = []
keys_received = []
keys_count = 0

def calc_polynomial_coeffs(secret):
    polynomial_coeffs[:, 0] = secret

def get_key(x):
    y = np.zeros(len(int_list), dtype=int)
    for j in range(len(int_list)):
        for i in range(k):
            y[j] = y[j] + polynomial_coeffs[j][i] * pow(x, i, P)
        y[j] = y[j] % P
    print(len(y))
    #print(y, '\n')
    key = np.zeros(128 * 128)
    key[0:M] = 255 * y / P
    print(key)
    key = key.reshape((128, 128))

    #key = key.reshape(128*128)
    #print(key[100])
    #print(y[100])

    return key


@bot.message_handler(commands=['start'])
def start_message(message):
    if message.chat.id not in users_list:
        users_list.append(message.chat.id)
    bot.send_message(message.chat.id,
                     'Welcome to Shamir Secret Bot! Type /get_key to obtain your part of secret key!')


@bot.message_handler(commands=['get_key'])
def send_key(message):
    if message.chat.id not in users_list:
        users_list.append(message.chat.id)
    x = users_list.index(message.chat.id) + 1
    key = get_key(x)

    img = Image.fromarray(key)
    img = img.convert("L")

    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    byte_im = buf.getvalue()

    bot.send_message(message.chat.id, 'This your part of the secret! Your ID is ' + str(x) + '!')
    bot.send_photo(message.chat.id, byte_im)

@bot.message_handler(content_types=['photo'])
def photo(message):
    global xs_received
    global keys_received
    global keys_count

    print(message.caption)
    print(len(message.photo))
    print(message.photo)

    if message.caption is not None:
        data = message.caption.split(' ')
        xs_received.append(int(data[0]))
        xs_received.append(int(data[1]))

    fileID = message.photo[-1].file_id
    file_info = bot.get_file(fileID)
    downloaded_file = bot.download_file(file_info.file_path)
    #bot.send_photo(message.chat.id, downloaded_file)


    img = Image.open(io.BytesIO(downloaded_file))
    img = img.convert("L")
    img_np = np.array(img,dtype=float)
    keys_received.append(img_np)
    keys_count = keys_count + 1

    if keys_count >= 2:
        secret_img = keys_to_secret(xs_received, keys_received)

        bot.send_photo(message.chat.id, secret_img)
        xs_received = []
        keys_received = []
        keys_count = 0


def keys_to_secret(xs, keys):
    y = np.zeros(M,dtype=int)
    for m in range(M):
        points = []
        for i in range(len(keys)):
            x = xs[i]
            key = keys[i]*P/255
            key = key.reshape(128*128)
            key = key[0:M]
            points.append((x,key[m]))
        y[m] = lagrange(points, P)

    secret_str = ''
    print(len(y))
    #print(y)
    for yi in range(len(y)):
        secret_str = secret_str + '{:04x}'.format(y[yi])

    print(len(secret_str))
    #print(secret_str)
    data = bytes.fromhex(secret_str)
    print(len(secret_str))
    print(len(data))
    return data

secret = int_list
calc_polynomial_coeffs(secret)

bot.polling()
