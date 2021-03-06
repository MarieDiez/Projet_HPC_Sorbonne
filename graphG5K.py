#! /usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import matplotlib.pyplot as plt
import numpy as np
import math
import operator
from collections import Counter
import json
import multiprocessing

cmd = ""
program = ""
step = 4

# file in which we save graph data
graphs = ""

# instances
list_instances = [
    "bell12.ec",
    "bell13.ec",
    "bell14.ec",
    "matching8.ec",
    "matching9.ec",
    "matching10.ec",
    "pentomino_6_10.ec",
    "pento_plus_tetra_2x4x10.ec"
]

def start_program(iter_min, iter_max, step, instance_file):
    next = 1
    prog_cmd = ""
    for i in range(iter_min, iter_max + 1, step):
        if local:
            os.environ["OMP_NUM_THREADS"] = str(i)
            prog_cmd = program + " --in instances/" + instance_file + " --progress-report 0 >> graphs/data.txt"
        else:
            prog_cmd = "mpirun -np " + str(i) + " --mca btl_base_warn_component_unused 0 -machinefile $OAR_NODEFILE " + program + " --in instances/" + instance_file + " --progress-report 0 >> graphs/data.txt"
            #prog_cmd = "mpirun -np " + str(i) + " " + program + " --in instances/" + instance_file + " --progress-report 0 >> graphs/data.txt"
        os.system(prog_cmd)
        print(prog_cmd)
        while(len(open('graphs/data.txt').readlines()) < next):
            time.sleep(0.01)
        next+=1
    return next

def fill_dico(fichier, nb_lines, t_seq):
    dico=dict()
    fichier.seek(0)
    for l in range(nb_lines - 1):
        line = fichier.readline()
        elems = line.split(" ")
        if local:
            dico[4 + (step * l)] = [float(t_seq) / float(elems[5].split('s')[0]), float(elems[5].split('s')[0])]
        else:
            dico[2 + (step * l)] = [float(t_seq) / float(elems[5].split('s')[0]), float(elems[5].split('s')[0])]
    return dico

def launch_graph(i, n):
    # on récupère le temps séquentiel
    instance_file = list_instances[i]
    fichier = open("graphs/data.txt", "a+")
    fichier.truncate(0)
    cmd = "./exact_cover_seq --in instances/" + instance_file + " --progress-report 0 >> graphs/data.txt"
    print(cmd)
    os.system(cmd)
    
    while(len(open('graphs/data.txt').readlines()) < 1):
        time.sleep(0.01)
    
    line = fichier.readline()
    elems = line.split(" ")
    t_seq = float(elems[5].split('s')[0])
    print("temps séqentiel = {}\n".format(t_seq))
    fichier.truncate(0)

    # lancement des commandes
    dicos = []
    nb_lines = 0
    if local:
        nb_lines = start_program(4, min(32, max_threads), 4, instance_file)
    else:
        nb_lines = start_program(iter_min, iter_max, step, instance_file)
    # remplir le dico
    d = fill_dico(fichier, nb_lines, t_seq)
    # ajouter à la collection de dicos
    dicos.append(d)

    # write
    graphs.write(str(t_seq) + " " + json.dumps(dicos) + " " + instance_file + '\n')

    fichier.truncate(0)
    fichier.close()

argLength = len(sys.argv)
num_machines = 0
max_threads = 0
local = True

if argLength == 2:
    if sys.argv[1] == "omp":
        program = "./exact_cover_omp"
        max_threads = multiprocessing.cpu_count()
        cmd = "make omp=1"
    else:
        quit()
elif argLength == 3:
    local = False
    if sys.argv[1] == "mpi":
        program = "./exact_cover_mpi"
        cmd = "make mpi=1"
    elif sys.argv[1] == "final":
        program = "./exact_cover_para"
        cmd = "make final=1"
    else:
        quit()
    num_machines = sys.argv[2]
    if(int(num_machines) <= 2):
        print("Erreur, il faut indiquer un nombre de travailleurs >= 3.\n")
        quit()
else:
    quit()

if not os.path.isdir(("graphs".format(os.getcwd()))):
    os.system("mkdir graphs")
if not os.path.isdir(("graphs/mpi".format(os.getcwd()))):
    os.system("mkdir graphs/mpi")
    os.system("mkdir graphs/mpi/delta_speed")
    os.system("mkdir graphs/mpi/exec")
if not os.path.isdir(("graphs/omp".format(os.getcwd()))):
    os.system("mkdir graphs/omp")
    os.system("mkdir graphs/omp/delta_speed")
    os.system("mkdir graphs/omp/exec")
if not os.path.isdir(("graphs/para".format(os.getcwd()))):
    os.system("mkdir graphs/para")
    os.system("mkdir graphs/para/delta_speed")
    os.system("mkdir graphs/para/exec")

graphs = open("graphs/graphs.txt", "w")

os.system("make")
os.system(cmd)

iter_min = 3
iter_max = int(num_machines)

if os.path.exists("graphs/data.txt"):
    os.system("rm graphs/data.txt")

for i in range(len(list_instances)):
    print("Start: {}".format(list_instances[i]))
    launch_graph(i, num_machines)
    print("End: {}\n".format(list_instances[i]))
