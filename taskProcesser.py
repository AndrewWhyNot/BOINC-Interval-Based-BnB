
import json
import subprocess
import MySQLdb as mdb

# check if should proceed tasks
should_proceed = False
try:
	conn = mdb.connect('localhost', 'boincadm', '', 'bnb')
	conn.set_character_set('utf8')
	cur = conn.cursor()
	req = 'select count(*) from result where server_state = 2;' # or server_state = 4;'
	cur.execute(req)
	res = cur.fetchone()
	if int(res[0]) <= 5: # or len(contents) >= 50:
		should_proceed = True
except mdb.Error as e:
	print(e.args[0],e.args[1])
finally:
	if conn:
		conn.close()
	#if should_proceed == False:
	#	import sys
	#	sys.exit("1")


tmp = str(subprocess.check_output(["ls", "-pR", "upload"])).replace("\\n\\n", "\\n").split("\\n")

# list of files formation
contents = []
dir = ""
for line in tmp:
        if len(line) == 0 or line[len(line)-1] == "/":
                continue
        if line[len(line)-1] == ":":
                dir = line.replace(":", "/")
                continue
        line = dir + line
        contents.append(line)


file = open("globMin", "r")
globMinData = file.read().replace("\n", "")
file.close()
globMinData = json.loads(globMinData)

file = open("in_files/next_task_num", "r")
taskNum = int(file.read().replace("\n", ""))
file.close()

proceeded_sets = []
file = open("proceeded_sets", "r")
proceeded_sets = file.read().split("\n")
file.close()

boxes = []
MAX_ITERS = 5000000000


# handling contents of uploaded files
for f in contents:
	try:
		file = open(f, "r")
		text = file.read().replace("\n", "")
		file.close()
		found = 0
		for i in range(len(proceeded_sets)):
			if text == proceeded_sets[i]:
				found = 1
				break
		if found == 1:
			subprocess.call(["rm", "-f", f])
			continue
	except subprocess.CalledProcessError:
                        #print("cannot access file!")
                        continue
	except FileNotFoundError:
			#print("file not found")
			continue
	if "directory" not in text:
		# parse file
		try:
			result = json.loads(text)
		except ValueError:
			#print("file contains not JSON!")
			continue
		proceeded_sets.append(text)
		globMinData["steps_performed"] += result["steps_performed"]
		if result["min_val"] < globMinData["globMin"]:
			# update globMin file and globMinData variable
			globMinData["globMin"] = result["min_val"]
			globMinData["arg"] = result["min_arg"]
			gMfile = open("globMin", "w")
			subprocess.call(["echo", json.dumps(globMinData)], stdout=gMfile)
			gMfile.close()
			subprocess.call(['/usr/bin/python3', '/home/andrey/bot.py', 'a_ignatov', '\"New min = ' + str(globMinData["globMin"]) + '\"'])
		boxes += result["parts"]

		# remove file f
		subprocess.call(["rm", "-f", f])


# concat with previous boxes
f = open('boxes')
boxes = json.loads(f.read())['boxes'] + boxes
f.close()


# removal of redundant boxes
eps = 0.1
def get_lb(b):
	bStr = str(b)[1:-1]
	lb = subprocess.Popen('./lb \"' + bStr + '\"', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
	lb = lb.decode('utf-8')[:-1]
	return float(lb)

boxes = [b for b in boxes if get_lb(b) <= globMinData["globMin"] - eps]


# creation of new tasks
if len(boxes) != 0 and should_proceed == True:
	taskDomains = [[boxes[i], boxes[len(boxes)//2 + i]] for i in range(len(boxes)//2)]
	if len(taskDomains)*2 != len(boxes):
		if len(taskDomains) == 0:
			taskDomains.append([boxes[0]])
		else:
			taskDomains[0].append(boxes[len(boxes)-1])

	itersNum = min((MAX_ITERS - globMinData["steps_performed"])//len(taskDomains), 100000)

	if itersNum != 0:
		for d in taskDomains:
			data = {"min_arg": globMinData["arg"],
				"min_val": globMinData["globMin"],
				"numIter": itersNum,
				"boxes": d}
			fileName = "in_files/task"+str(taskNum)+".txt"
			newF = open(fileName, "w")
			subprocess.call(["echo", json.dumps(data)], stdout=newF)
			newF.close()
			subprocess.call(["./bin/stage_file", "--copy", fileName])
			subprocess.call(["./bin/create_work", "--appname", "bnb_app", "--wu_name", "task"+str(taskNum), "task"+str(taskNum)+".txt"])
			taskNum += 1
	else:
		globMinData["left_domains"] = taskDomains

	f = open('boxes', 'w')
	s = {'boxes' : []}
	f.write(json.dumps(s))
	f.close()
else:
	if should_proceed == False:
		f = open('boxes', 'w')
		s = {'boxes' : boxes}
		f.write(json.dumps(s))
		f.close()




gMfile = open("globMin", "w")
subprocess.call(["echo", json.dumps(globMinData)], stdout=gMfile)
gMfile.close()

g = open("in_files/next_task_num", "w")
g.write(str(taskNum))
#subprocess.call(["echo", taskNum], stdout=g)
g.close()

file = open("proceeded_sets", "w")
for set in proceeded_sets:
	if len(set) != 0:
		file.write("%s\n" % set)
file.close()

if len(boxes) != 0:
        import time
        time.sleep(5)

f = open('problem_time')
timeData = json.loads(f.read())
f.close()



# mysql check of results status
#import MySQLdb as mdb

APP_VERSION = '210'
exit_res = "90"
try:
        conn = mdb.connect('localhost', 'boincadm', '', 'bnb')
        conn.set_character_set('utf8')
        cur = conn.cursor()
        req = 'select distinct server_state from result;' #, outcome, client_state from result;' # where app_version_num = ' + APP_VERSION + ';'
        cur.execute(req)
        res = cur.fetchall()
        #print('MySQL ans: ', res)
        if len(res) == 1:
                #print(type(res[0]))
                #if res[0] ==  (5, 1, 5):
                if res[0][0] ==  5:
                        exit_res = "0"
                        import time
                        timeData['end'] = time.time()
                        timeData['time'] = (timeData['end'] - timeData['st']) / 60
                        timeData['rel_time'] = timeData['time'] / globMinData["steps_performed"]
                        f = open('problem_time', 'w')
                        f.write(json.dumps(timeData))
                        f.close()
                else:
                        if res[0][0] == 2:
                                exit_res = "1"
                        else:
                                if timeData['st'] == -1:
                                        import time
                                        timeData['st'] = time.time()
                                        f = open('problem_time', 'w')
                                        f.write(json.dumps(timeData))
                                        f.close()
                                        exit_res = "25"
        else:
                if timeData['st'] == -1:
                        import time
                        timeData['st'] = time.time()
                        f = open('problem_time', 'w')
                        f.write(json.dumps(timeData))
                        f.close()
                        exit_res = "25"
except mdb.Error as e:
        print(e.args[0],e.args[1])
finally:
	if conn:
		conn.close()


# removal of redundant unhandled tasks
def get_lb_for_set(s):
	m = 10000
	for el in s:
		lb = get_lb(el)
		if lb < m:
			m = lb
	return m

try:
	conn = mdb.connect('localhost', 'boincadm', '', 'bnb')
	conn.set_character_set('utf8')
	cur = conn.cursor()
	req = 'select distinct workunit.id, workunit.name from (workunit inner join result on workunit.id = result.workunitid) where server_state = 2 or server_state = 4;' #and outcome <> 5;'
	cur.execute(req)
	res = cur.fetchall()
	for line in res:
		f = open('in_files/' + line[1] + '.txt')
		js = json.loads(f.read())
		f.close()
		if get_lb_for_set(js['boxes']) > globMinData["globMin"] - eps:
			try:
				check_req = 'select distinct server_state from result where workunitid = \'' + str(line[0]) + '\';'
				cur.execute(check_req)
				states = [int(l[0]) for l in cur.fetchall()]
				#print('states for wu = ', str(line[0]), ': ', states)
				#if 4 not in states:
				subprocess.call(['./bin/cancel_jobs', '--name', line[1]])
			except mdb.Error as e:
				print(e.args[0],e.args[1])
except mdb.Error as e:
	print(e.args[0],e.args[1])
finally:
	if conn:
		conn.close()




#print(exit_res)
import sys
#sys.exit(exit_res)
if exit_res != "0":
	sys.exit("1")
sys.exit("0")
