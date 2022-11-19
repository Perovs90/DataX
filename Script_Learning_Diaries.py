from os import listdir, chdir, path, getcwd
import glob
import json
from collections import defaultdict
import pandas as pd
from statistics import median

owd = getcwd()
owd = "C:/Users/perov/DataX"
mypath = "C:/Users/perov/DataX/Submission_ALL_week_2_2"
num_questions = 6
week = 2
#to get working directory


#Function sort_submissions() takes your working directory(owd), path to the folder with submissions (mypath),
# number of questions in the current learning diary and week number as arguments.
# The function returns several lists as output:
# 1) not processed files (not_processed) that contains names of submitted directories without any .ipynb files
# 2) wrongly formatted files (wrong_format) which have other than json structure even if they are saved as .ipynb files
# 3) wrong notebooks (wrong_notebooks). It means the submitted files have .ipynb format but have
# different then Learning Diary structure. The main criterion is based on the length of the notebook.
# 4) suspicious submissions (suspicious_submissions). Submitted files have empty answers, deleted questions
# or any weird alterations. We need it for grading function
# 5) all names of the students who have submitted anything (all_names). We need it for grading function
# After execution the function creates two csv files in your working directory: " answers_week_{number_of_the_week}.csv'
#  and "suspiscious_week_{number_of_the_week}.csv"

def sort_submissions(owd, mypath, num_questions, week = 2):
    #getting access to directories
    directories = [d for d in listdir(mypath) if path.isdir(mypath + '/' +  d + '/')]
    #creating lists of questions:
    questions_eng = [f'Question {x+1}' for x in range(num_questions)]
    questions_ger = [f'Frage {x+1}' for x in range(num_questions)]
    #creating a dictionary to check english version too:
    questions_dict = dict(zip(questions_ger, questions_eng))
    #creating lists of answers:
    answer_ger = [f'Antwort {x+1}:' for x in range(num_questions)]
    answer_eng = [f'Answer {x+1}:' for x in range(num_questions)]
    #creating dictionaries to go from question to answer
    question_answer_ger_dict = dict(zip(questions_ger, answer_ger))
    question_answer_eng_dict = dict(zip(questions_ger, answer_eng))
    answers_dict = defaultdict(list) #dictionary to put the answers there
    name_cells_amount_dict = {} #to trace number of cells in the notebook
    names = []
    all_names = []
    d_empty_dict = defaultdict(list) #dictionary of empty cells
    d_empty_dict_ind = {}
    suspicious_submissions = [] #list of names of people who submitted wrongly
    filenames_list = [] #names of files with jupiter notebooks
    not_processed = []
    not_processed_names = []
    wrong_format = [] #the list of the files which have other than json structure even if they are saved .ipynb
    #iterate over all directories
    for d in directories:
        name = d.partition('_')[0]#get name of the person from directory name
        all_names.append(name)
        chdir(mypath + '/' + d)
        not_processed.append(d)
        not_processed_names.append(name)
        if len(glob.glob("*.ipynb")) < 1:
            continue
        file_name =  glob.glob("*.ipynb")[-1]
        filenames_list.append(file_name)
        #if len(glob.glob("*.ipynb")) > 1:
        #    print(d +'- submitted more than 1 file')
        with open(file_name, 'r') as myfile:
            data=myfile.read()#read ipynb file (json)
        if not data.startswith("{"):#check if the file is json file
            wrong_format.append(d)
            continue
        #if we got here, it means we managed to process data in ipynbformat, therefore:
        not_processed.remove(d)
        not_processed_names.remove(name)
        names.append(name)
        obj = json.loads(data) # transform string-json to dictionary
        #iterate over all questions
        questions_list = list(questions_dict.keys())
        questions_remained = questions_list.copy()# creatiing a copy of all questions to spot missing ones
        for ind, question in enumerate(questions_list):
            cell_count = 0 #to count amount of cells
            #iterate over all cells in the file
            for i in range(len(obj['cells']) - 1): #iterate over all cells of the file
                cell_count += 1
                for line in obj['cells'][i]['source']:
                    if ((question + ":") in line) or ((questions_dict[question] + ":") in line):
                        questions_remained.remove(question)
                        joint_string = " ".join(obj['cells'][i+1]['source'])
                        #following statement is for the situation when answer is in the next cell after "Antwort :"
                        if ((joint_string == question_answer_ger_dict[question]) or
                            (joint_string == question_answer_eng_dict[question]) or
                            (joint_string == question_answer_ger_dict[question] + ' ') or
                            (joint_string == question_answer_eng_dict[question]  + ' ') or
                            joint_string == ''):
                            if i+1 < len(obj['cells'])-1 :
                                if ind < len(questions_list) - 1:
                                    joint_string_2 = " ".join(obj['cells'][i+2]['source'])
                                    if not (((questions_dict[questions_list[ind+1]] + ':') in joint_string_2) or
                                        ((questions_list[ind+1] + ':') in joint_string_2)):
                                        joint_string = joint_string_2
                                    else:
                                        joint_string = " ".join(obj['cells'][i+1]['source'])
                                else:
                                    joint_string = " ".join(obj['cells'][i+2]['source'])
                        if (0 < len(joint_string.split()) < 5):
                            if name not in suspicious_submissions:
                                    suspicious_submissions += [name]
                        answers_dict[question] += [joint_string]
                        cell_count += 1
                        if joint_string == '':
                            d_empty_dict[d] += [question]
                            d_empty_dict_ind[d] = len(answers_dict[question]) - 1
        name_cells_amount_dict[name] = len(obj['cells'])
        #To mark questions that are missing in the document:
        for question in questions_remained:
            answers_dict[question] += ["DOES NOT EXIST"]
            if name not in suspicious_submissions:
                suspicious_submissions += [name]

    #check the situation when student moved the cell from the place after corresponding question:
    for d in d_empty_dict.keys():
        name = d.partition('_')[0]
        chdir(mypath + '/' + d)
        file_name =  glob.glob("*.ipynb")[0]
        with open(file_name, 'r') as myfile:
            data=myfile.read() # read ipynb file (json)
        obj = json.loads(data) # transform json to dictionary
        questions_list = list(questions_dict.keys())
        for ind, question in enumerate(questions_list):
            joint_string = None
            for i in range(len(obj['cells']) - 1):
                for line in obj['cells'][i]['source']:
                    if ((question_answer_ger_dict[question] in line) or (question_answer_eng_dict[question] in line) or
                        ((question_answer_ger_dict[question] + ' ') in line) or ((question_answer_eng_dict[question]  + ' ') in line)):
                        joint_string = " ".join(obj['cells'][i]['source'])
                        if i < len(obj['cells']) - 1 :
                            if ind+1 < len(questions_list)-1:
                                if not (((questions_dict[questions_list[ind+1]] + ':') in obj['cells'][i+1]['source']) or
                                     ((questions_list[ind+1] + ':') in obj['cells'][i+1]['source'])):
                                    joint_string = " ".join(obj['cells'][i+1]['source'])
                            else:
                                joint_string = " ".join(obj['cells'][i+1]['source'])
                        answers_dict[question][d_empty_dict_ind[d]] = joint_string
            if joint_string == None:
                suspicious_submissions += [name]
    median_amount = median(name_cells_amount_dict.items())[1]
    #to find wrong notebooks that obviously have another structure than learning diary:
    wrong_notebooks = []
    for name in names:
        if median_amount*0.6 > name_cells_amount_dict[name] or name_cells_amount_dict[name] >  median_amount*2:
            wrong_notebooks.append(name)
            #names.remove(name)
            print(name + '- submitted wrong notebook')
            #names.remove(name)
    #to separate wrong notebooks from suspicious submissions
    for name in wrong_notebooks:
        if name in suspicious_submissions:
            suspicious_submissions.remove(name)
    #preparing the DataFrame
    names_dict = {'Name': names}
    final_dict = names_dict.copy()
    #merge names and answers:
    final_dict.update(answers_dict)
    #create the dataframe:
    answers_df = pd.DataFrame.from_dict(final_dict)
    answers_df = answers_df.set_index('Name')
    #creating the dataframe with only suspicious submissions:
    suspiscious_df = answers_df.loc[suspicious_submissions, :]
    #write csv to the working directory
    chdir(owd)
    answers_df.to_csv(f'answers_week_{week}.csv')
    suspiscious_df.to_csv(f'suspiscious_week_{week}.csv')
    return not_processed, wrong_format, wrong_notebooks, suspicious_submissions, all_names

#apply the function
not_processed, wrong_format, wrong_notebooks, suspicious_submissions, all_names = sort_submissions(owd, mypath, num_questions, week = 3)


###SCRIPT for GRADING:
path_eng = 'Grades-Python-EN-Learning Diary.csv'
path_de = 'Grades-Python-DE-Learning Diary.csv'
bad_submissions = ['Emma Zollner', 'Lara Albrecht', 'Leonie Schlicht', 'mario kovacs',
                   'Rafal Zukowski', 'Lys-Frederik Nack', 'Marc Nielsen', 'William Pogadl', 'Jan Karl Keller']

#The function grading_func(owd, path_eng, path_de, all_names, bad_submissions) takes as arguments: your working directory(owd),
# path to the grading lists (path_eng, path_de), list of names that were analyzed by the function sort_submissions() (all_names),
# and manually created list of bad submissions that deserves 0 points
# list contains people from not_processed, wrong_format, wrong_notebooks, suspicious_submissions)
#The output of the function is two files with grades: 'Graded_Diaries_ENG.csv', 'Graded_Diaries_DE.csv'
def grading_func(owd, path_eng, path_de, all_names, bad_submissions):
    grades_eng = pd.read_csv(path_eng)
    grades_de = pd.read_csv(path_de)
    ### International students
    grades_eng.loc[:, 'Grade'] = int(0) #assign 0 to all
    submitted = grades_eng['Full name'].isin(all_names) #distinguish as submitted all analyzed submissions
    grades_eng.loc[submitted, 'Grade'] = 100 #assign 100 to all analyzed
    submitted_but_badly = grades_eng['Full name'].isin(bad_submissions) #distinguish bad submissions among submitted
    grades_eng.loc[submitted_but_badly, 'Grade'] = 0 #assign 0 to bad submissions
    ### German students
    grades_de.loc[:, 'Grade'] = int(0)
    submitted = grades_de['Full name'].isin(all_names)
    grades_de.loc[submitted, 'Grade'] = int(100)
    submitted_but_badly = grades_de['Full name'].isin(bad_submissions)
    grades_de.loc[submitted_but_badly, 'Grade'] = 0
    #Creating the csv:
    chdir(owd)
    grades_eng.to_csv('Graded_Diaries_ENG.csv')
    grades_de.to_csv('Graded_Diaries_DE.csv')

grading_func(owd, path_eng, path_de, all_names, bad_submissions)


