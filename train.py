import os, glob, pickle, argparse, re
import numpy as np
from fractions import Fraction


class Word:
    def __init__(self, value: str = '*'):
        self.value = value
        self.counter = 1
        self.next = dict()

    def findNext(self, nextWord: str):
        """ Вызывается при анализе текста, если в тексте после этого слова следует nextWord. Возвращает объект Word """

        if nextWord in self.next:
            self.next[nextWord].counter += 1
            return self.next[nextWord]
        newWord = Word(nextWord)
        self.next[nextWord] = newWord
        return newWord

    def pickNext(self):
        """
        Вызывается для случайного выбора следующего слова.
        Возвращает объект Word.
        Если словарь next пустой, то возвращает None
        """

        if len(self.next.keys()) == 0:
            return None

        nextWords = []
        for key in self.next.keys():
            nextWords.append(key)
        frequency = [Fraction(self.next[nextWord].counter, self.counter) for nextWord in nextWords]
        if sum(frequency) == 1:  # все вычисления вероятностей прошли хорошо
            nextWord = np.random.choice(nextWords, p = frequency)
        else:
            # один раз вылетела ошибка при тестировании, что сумма вероятностей не 1
            nextWord = np.random.choice(nextWords)
        return self.next[nextWord]

class NModel:
    @staticmethod
    def __getText(textPath: str = '') -> str:
        """ Т.к. текстовые файлы могут быть в разных кодировках, пытаемся их считать во всех самых распространённых """

        if textPath == '':
            return ''
        codes = ['utf-8', 'ANSI', 'ASCII']
        for code in codes:
            try:
                with open(textPath, 'r', encoding=code) as textFile:
                    text = textFile.read()
                return text
            except UnicodeDecodeError:  # не смогли прочитать какой-то символ
                continue
        return ''  # не смогли подобрать кодировку

    @staticmethod
    def __parseText(textPath: str = ''):
        """ Считываем текст из файла, ищем русские слова, приводим их к нижнему регистру и возвращаем numpy-массив """

        if not os.path.exists(textPath):  # вводим текст через консоль
            text = ''
            print("Вводите обучающий текст построчно. Чтение окончится, когда вы введёте пустую строку:\n>>", end='')
            s = input()
            while s:  # пока не ввели пустую строку
                text += s + '\n'
                s = input('>>')
        else:
            text = NModel.__getText(textPath)
        words = np.array(re.split(r'[^а-яё]+', text.lower(), flags=re.IGNORECASE))
        condition = words != ''
        words = np.extract(condition, words)  # удалим пустые строки
        return words

    def __init__(self, Nmax: int = 10):
        self.Nmax = max(2, Nmax)  # нет смысла рассматривать меньше 2 слов в фразе
        self.NGram = Word('*')
        self.NGram.counter = 0
        self.alreadyKnown = []

    def fit(self, textPath: str = ''):
        """ Обучаем модель на основе какого-то текста """

        if textPath in self.alreadyKnown:
            return
        if os.path.exists(textPath):
            self.alreadyKnown.append(textPath)
        words = self.__parseText(textPath)
        self.NGram.counter += len(words)  # увеличиваем счётчик общего количества проанализированных слов за всё время
        curWord = self.NGram  # стартуем с пустой фразы
        curIndex = 0  # индекс текущего слова в списке слов из анализируемого текста
        while curIndex != len(words):
            phraseLength = 1  # сколько слов в анализируемой фразе, которая начинается с words[curIndex]
            while phraseLength <= self.Nmax and curIndex != len(words):
                curWord = curWord.findNext(words[curIndex])  # нашли объект-слово или создали его в списке следующих слов
                # попробуем добавить ещё одно слово в фразу
                curIndex += 1
                phraseLength += 1
            # Перебрали фразы всех возможных длин с фиксированным первым словом из текста
            # delta(curIndex) = delta(phraseLenght) = phraseLenght - 1, нам нужно вернуть curIndex к тому значению
            # с какого слова начиналась наша фраза и прибавить один, чтобы начать анализировать фразы со следующим
            # первым словом из текста. curIndex - (phraseLenght - 1) + 1 = curIndex - phraseLenght + 2
            curIndex = curIndex - (phraseLength - 1) + 1
            curWord = self.NGram  # опять стартуем с пустой фразы
        return

    def generate(self, firstWord: str = '*', length: int = 1) -> str:
        """ Генерирует фразу с начальным словом prefix длиной length """

        if length < 1:
            return ''

        answer = []  # слова для возвращаемой сгенерированной фразы
        answerLength = 0  # сколько слов уже сгенерировали
        curWord = self.NGram  # пока что префикс пустой
        if firstWord == '*':
            # если не задано первое слово - выбираем его случайно
            curWord = curWord.pickNext()
            if curWord is None:
                print("ПУСТАЯ МОДЕЛЬ. НЕВОЗМОЖНО СОСТАВИТЬ ФРАЗУ!!!")
                return ''
            firstWord = curWord.value
        firstWord = firstWord.lower()
        answer.append(firstWord)  # добавили первое слово и не важно, известно ли оно модели или нет
        answerLength += 1
        if length == 1:
            return answer[0]

        # Введём длину префикса, на основе которого выбирается следующее слово.
        # По сути, сколько последних сгенерированных слов учитываются при выборе следующего слова
        prefixLength = 1
        if firstWord not in self.NGram.next:
            # ввели первое слово, которое не известно модели и хотим длину >1, тогда выберем второе слово случайно
            curWord = self.NGram.pickNext()
            answer.append(curWord.value)
            answerLength += 1
        else:
            curWord = self.NGram.next[firstWord]

        while answerLength != length:
            # дополняем наш префикс до максимума
            while prefixLength < self.Nmax and answerLength != length:
                curWord = curWord.pickNext()
                if curWord is None:  # не смогли найти следующее слово
                    break
                answer.append(curWord.value)
                prefixLength += 1
                answerLength += 1
            word = answer[-1]
            curWord = self.NGram.next[word]  # стартуем с последнего сгенерированного слова
            prefixLength = 1

        return ' '.join(answer)


def parseTrain():
    """ Возвращает имя файла модели и массив имён файлов для записи """

    # Парсим консольный вызов
    trainParser = argparse.ArgumentParser(description='Обучение N-граммной модели на основе текстов')
    trainParser.add_argument('--input-dir', dest='textDir', type=str, default='',
                             help='Имя директории с коллекцией обучающих текстов. Стандартно - консольный ввод текста')
    trainParser.add_argument('--model', dest='modelPath', type=str, default='',
                             help='Путь к файлу, в который сохраняется модель')
    args = trainParser.parse_args()

    # Обработка введённого пути к файлу с моделью
    if not args.modelPath:  # не передали путь к файлу с моделью
        args.modelPath = input("Введите путь к файлу с моделью: ")
    if not os.path.exists(args.modelPath):  # такого файла ещё не существует, создадим пустую модель
        print("Такой модели ещё не было. Создана новая модель для обучения")
        newModel = NModel()
        with open(args.modelPath, 'wb') as newFile:
            pickle.dump(newModel, newFile)
    # Обработка директории с текстами для обучения
    textPathes = []
    if not args.textDir:  # текст вводится через консоль
        print("Ввод обучающего текста будет осуществляться через консоль")
        textPathes.append('')
    elif not os.path.exists(args.textDir):  # такой папки не существует, скажем пользователю ввести текст в консоль
        print("Такой папки не существует\nВвод обучающего текста будет осуществляться через консоль")
        textPathes.append('')
    else:
        # получаем список путей к ТЕКСТОВЫМ файлам в указанной папке
        textPathes = glob.glob(args.textDir+'\\*.txt')
        # заменим все пути на абсолютные для запоминания путей изученных файлов
        for i in range(len(textPathes)):
            textPathes[i] = os.path.abspath(textPathes[i])
    return args.modelPath, textPathes

def main():
    modelPath, textPathes = parseTrain()
    with open(modelPath, 'rb') as modelFile:
        model = pickle.load(modelFile)
    for textPath in textPathes:
        model.fit(textPath)
        print("Файл {} успешно изучен".format(textPath))
    print("Сеанс обучения окончен")
    with open(modelPath, 'wb') as modelFile:
        pickle.dump(model, modelFile)
    print("Данные сохранены")


if __name__ == "__main__":
    main()