import pandas as pd
import numpy as np
from anytree import Node
from anytree.exporter import DotExporter
import pydot

class Bayes:
    def __init__(self, data, interval, bias):
        self.P_E = []             # probability of assumption E
        self.P_HE = []            # probability of conclusion H if the assumption E is correct
        self.P_HnE = []           # probability of conclusion H if the assumption E is incorrect
        self.Guess = []           # guess by expert on interval <>
        self.Interval_Start = []  # the left side of on interval
        self.Interval_End = []    # the right side of an interval
        self.P_H = []             # probability of conclusion H

        self.P_H.append(bias)
        self.Interval_Start.append(interval[0])
        self.Interval_End.append(interval[-1])

        for line in data:
            self.P_E.append(line[0])
            self.P_HE.append(line[1])
            self.P_HnE.append(line[2])
            self.Guess.append(line[3])


        if (len(self.P_E) != len(self.P_HE)) and  (len(self.P_E) != len(self.P_HnE)) and (len(self.P_E) != len(self.Guess)):
            raise Exception("The incorrect number of values!")
        elif (len(self.P_HE) != len(self.P_HnE)) and (len(self.P_HE) != len(self.Guess)):
            raise Exception("The incorrect number of values!")
        elif (len(self.P_HnE) != len(self.Guess)):
            raise Exception("The incorrect number of values!")
        elif (len(self.Interval_Start) != len(self.Interval_End)):
            raise Exception("The incorrect number of values!")
        elif len(self.P_H) != 1:
            raise Exception("The incorrect number of values!")


    def subjective_bayes_method(self, p_e, guess, interval_start, interval_end):
        if interval_start <= guess <= 0:
            result = p_e + (p_e / abs(interval_start)) * guess
            result = round(result, 4)
        elif 0 < guess <= interval_end:
            result = p_e + ((1 - p_e) / abs(interval_start)) * guess
            result = round(result, 4)
        else:
            raise Exception("The number guess is out of interval!")

        print("Subjective Bayesian function: ", result)
        return result


    def combined_CTR(self, p_ee, p_e, p_he, p_hne, p_h):
        if 0 <= p_ee <= p_e:
            result = p_hne + ((p_h - p_hne) / p_e) * p_ee
            result = round(result, 4)
        elif p_e <= p_ee <= 1:
            result = p_h + ((p_he - p_h) / (1 - p_e)) * (p_ee - p_e)
            result = round(result, 4)

        print("CTR combination function: ", result)
        return result


    def chance(self, p_he):
        result = p_he / (1 - p_he)
        result = round(result, 4)
        print("Chance function: ", result)
        return result


    def logicalSufficiency(self, o_he, o_h):
        result = o_he / o_h
        result = round(result, 4)
        print("Logical sufficiency function: ", result)
        return result


    def combined_GLOB(self, ls, o_h):
        semi_result = 1
        for i in range(len(ls)):
            semi_result = semi_result * ls[i]

        result = semi_result * o_h
        result = round(result, 4)
        print("\nGLOB combination function: ", result)
        return result


    def probability(self, glob):
        result = glob / (1 + glob)
        result = round(result, 4)
        print("Probability function: ", result)
        return result


    def combined_calculation(self):
        P_EEap = []
        P_HEap = []
        O_HEap = []
        Ls = []

        print("P(E): ", self.P_E)
        print("P(HE): ",self.P_HE)
        print("P(HnE): ",self.P_HnE)
        print("P(Guess): ",self.Guess)
        print("P(Interval_Start): ", self.Interval_Start)
        print("P(Interval_end): ", self.Interval_End)
        print("P(H): ", self.P_H)
        print()

        for i in range(len(self.P_E)):
            P_EEap.append(self.subjective_bayes_method(self.P_E[i], self.Guess[i], self.Interval_Start[0], self.Interval_End[0]))
        print()

        for i in range(len(self.P_E)):
            P_HEap.append(self.combined_CTR(P_EEap[i], self.P_E[i], self.P_HE[i], self.P_HnE[i], self.P_H[0]))
        print()

        for i in range(len(self.P_E)):
            O_HEap.append(self.chance(P_HEap[i]))
        O_H = self.chance(self.P_H[0])
        print()

        for i in range(len(self.P_E)):
            Ls.append(self.logicalSufficiency(O_HEap[i], O_H))

        glob = self.combined_GLOB(Ls, O_H)
        print()

        final = self.probability(glob)

        return P_EEap,P_HEap,O_HEap,Ls,glob,final
    
    def program(self):
        result = self.combined_calculation()
        
        #Visualization
        root = Node("Data")
        for i in range(0,len(result[0])):
            label_bayes = "Bayes {}".format(result[0][i])
            label_ctr = "CTR {}".format(result[1][i])
            label_chance = "Chance {}".format(result[2][i])
            label_suff = "Sufficiency {}".format(result[3][i])
            label_glob = "Glob {}".format(result[4])
            label_prob = "Probability {}".format(result[5])
            
            bayes = Node(label_bayes,parent = root)
            ctr = Node(label_ctr,parent = bayes)
            prob = Node(label_chance,parent = ctr)
            logsuff = Node(label_suff,parent = prob) 
            glob = Node(label_glob,parent = logsuff) 
            prob = Node(label_prob,parent = glob)
            
        
        #for line in DotExporter(root):
        #    print(line)
        
        DotExporter(root).to_dotfile("tree.dot")
        (graph,) = pydot.graph_from_dot_file('tree.dot')
        graph.write_png('tree.png')


def getData(path):
    file = open(path, "r")

    lines = file.readlines()

    bias = float(lines[0])

    interval = lines[1].strip('\n').split(",")

    interval = [float(i) for i in interval]

    data = []
    for i in range(2, len(lines)):
        temp = lines[i].strip('\n').split(",")
        temp = [float(j) for j in temp]
        data.append(temp)

    return bias, interval, data
        
        
if __name__ == "__main__":
    #bias, interval, data = getData("data1.txt")
    #bayes1 = Bayes(data, interval, bias)
    #bayes1.program()

    bias, interval, data = getData("data2.txt")
    bayes2 = Bayes(data, interval, bias)
    bayes2.program()

    #bias, interval, data = getData("data3.txt")
    #bayes3 = Bayes(data, interval, bias)
    #bayes3.program()
