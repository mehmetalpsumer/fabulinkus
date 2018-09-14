# -*- coding: utf-8 -*-
import sys
import time
import codecs
from operator import itemgetter


class Word:
    def __init__(self, min_frequency=0):
        with codecs.open('words_list.txt', 'r', encoding='utf-8') as word_file:
            i = 0  # Ignore first 6 lines
            words_list = []  # Initialize list
            for line in word_file:
                if i > 6 and (int(line.split()[3]) > min_frequency):
                    # Store as tuple (word, frequency)
                    word_data = (line.split()[0].encode('utf-8'), int(line.split()[3]))
                    words_list.append(word_data)
                i += 1
        self.sorted_words_list = sorted(words_list, key=itemgetter(
            1), reverse=True)  # Sort by frequency, descending
    def predict(self, query=None, max_length=20):
        '''
        PARAMETERS
            string query => The prefix to be searched, if not given then top words will be returned in overall (ve, ile, için...)
            max_length => Max characters to fit in display screen, result number will vary
        RETURNS
            display_list => Tuple (word, frequency) with desired values
        '''
        predict_start_time = time.time()  # Execute time variable

        if query is None:  # If no parameter is given, return top words
            top_words = self.sorted_words_list[:5]
        else:
            top_words = []
            for word in self.sorted_words_list:
                if word[0].startswith(query):
                    top_words.append(word)
                if len(top_words) is 5:
                    break

        display_list = []
        character_counter = 0  # Count total characters to determine if we stop or get more words as output
        for word in top_words:
            if (len(word[0])+character_counter) <= max_length:
                #print("INFO:: New word found => {}".format(word[0]))
                #print("DEBUG:: counter = {}, word_length = {}, max = {} ".format(character_counter, len(word[0]), max_length))
                display_list.append(word)
                character_counter += len(word[0])

        # Display results
        print("::DEBUG RESULTS::")
        print("Query: {}".format(query))
        print("Result length: {}".format(len(display_list)))
        for result in display_list:
            print("    Result: {}".format(result[0]))
        print("Predict execution time {}s".format(time.time() - predict_start_time))
        print("::END::")

        return display_list
