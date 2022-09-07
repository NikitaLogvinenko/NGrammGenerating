import os, glob, pickle, argparse, re
import numpy as np
from fractions import Fraction
from time import time
from math import floor
from train import Word, NModel

def parseGenerate():
    """ Возвращает имя файла модели, первое слово и длину генерируемой строки """

    # Парсим консольный вызов
    generateParser = argparse.ArgumentParser(description='Генерация текстов заданной длины')
    generateParser.add_argument('--model', dest='modelPath', type=str, default='',
                             help='Путь к файлу с используемой моделью')
    generateParser.add_argument('--prefix', dest='firstWord', type=str, default='*',
                             help='Первое слово, с которого начать генерацию строки (необязательный параметр)')
    generateParser.add_argument('--length', type=int, default=1,
                                help='Длина генерируемой строки')
    args = generateParser.parse_args()

    # Обработка введённого пути к файлу с моделью
    while not os.path.exists(args.modelPath):
        print("Такой модели не существует. Введите путь к файлу с моделью\n>>", end='')
        args.modelPath = input()
    # Обработка директории с текстами для обучения
    return args.modelPath, args.firstWord, args.length

def main():
    np.random.seed(floor(time()))  # инициализируем генератор случайных чисел текущим временем в секундах с 01.01.1970
    modelPath, firstWord, length = parseGenerate()
    with open(modelPath, 'rb') as modelFile:
        model = pickle.load(modelFile)
    string = model.generate(firstWord, length)
    print("Результат генерации:", string, sep='\n')

if __name__ == "__main__":
    main()
