import datetime
from filecmp import dircmp
import os
import sys
from pathlib import Path
import random
import shutil
from graphviz import Digraph
#----------------------------------------------
#------------HELPERS FUNCTION------------------
#----------------------------------------------
def get_wit_path(path): 
    '''Help function to Wit- getting as argument absolute path of CWD
    and returning the path to .wit directory or False if .wit not exist in any of
    the parent directories of CWD

    Args:
        path (class 'pathlib.WindowsPath'): path to search .wit in one of it parents dir
    
    Returns:
        path_to_wit (class 'pathlib.WindowsPath') : path to the closest .wit dir from parents dirs of path
        OR:
        False (bool): if there is no .wit dir in any of path parent dirs
    '''
    is_root = path / '.wit'
    if is_root.exists():
       return is_root
    for parent in Path(path).parents:
        path_to_wit = parent / '.wit'
        if path_to_wit.exists():
            return(path_to_wit)   
    return False    

def compare_dics(a, b):
    '''
    function used in wit- taking two directories and return the files and dirs exist only in a dir
    and files and dirs exist both in a and b but with different content

    Args:
        a(Class<Pathlib class>) : left directory
        b(Class<Pathlib class>) : right directory
    Returns:
        return_list(list) : list of all only in a and different between a and b files and directories
    '''
    d_cmp = dircmp(a, b)
    return_list = []
    #add to list files only in a dir
    for name in d_cmp.left_only:
        name_path = a / name
        return_list.append(str(name_path))
    #add to list files with different content in a and b
    for name in d_cmp.diff_files:
        name_path = a / name
        return_list.append(str(name_path))
    #compare all sub directories exist in both folders
    for sub_dir in d_cmp.subdirs:
        return_list.extend(compare_dics(a / sub_dir, b / sub_dir))
    return(return_list) 

def remove_staging_cont(staging_path, include=False):
    '''removing all staging area content, optionally removing also the staging area folder
    Args:
        staging_path(Class <Pathlib class>) : the Path to the staging area directory

        include(bool) : optional, if True- delete also the staging are folder
    Returns:
        None
    '''
    for sub in staging_path.iterdir():
            if sub.is_dir():
                shutil.rmtree(sub)
            else:
                sub.unlink()
    if include:
        shutil.rmtree(staging_path)

def check_wit_init():
    '''checking if  wit is inittialized in cwd, if init- returns the path to wit and to cwd,
    if not- print message and exit

    Args:
        None
    Returns:
        path_to_wit(class 'pathlib.WindowsPath') : path to the closest .wit dir from parents dirs of path

        cwd_path(class 'pathlib.WindowsPath') : path to the current work directory
    '''
    cwd_path = Path(os.getcwd())
    path_to_wit = get_wit_path(cwd_path.resolve())
    if not path_to_wit:
        print('Wit directory not found in the parents of cwd')
        sys.exit()
    return (path_to_wit, cwd_path)
#---------------------------------------------
#------------INIT FUNCTION---------------------
#----------------------------------------------
def init()-> None:
    '''initiate .wit folder in cwd. creating stging area, images dir and active branch file'''
    cwd = os.getcwd()
    os.mkdir(cwd + '\.wit')
    os.mkdir(cwd + '\.wit\staging_area')
    os.mkdir(cwd + '\.wit\images')
    activate = cwd + '\.wit\\activated.txt'
    with open(activate ,'w') as active_branch:
        active_branch.write('master')
#----------------------------------------------
#------------ADD FUNCTION----------------------
#----------------------------------------------
def add(add_obj):
    path_to_wit, cwd_path = check_wit_init()
    add_obj_path = Path(add_obj)
    if add_obj_path.resolve() == cwd_path.resolve():
        staging = path_to_wit / 'staging_area'
        remove_staging_cont(staging)
        for sub in add_obj_path.iterdir():
            sub_path = add_obj_path.resolve() / sub
            if sub.is_dir() and str(sub) != '.wit':
                shutil.copytree(sub.resolve(), staging / sub)
            elif sub.is_file():
                shutil.copy2(sub.resolve(), (staging / sub).parent)
        sys.exit()
    relative_to_wit = Path(add_obj_path.resolve().relative_to(path_to_wit.parent))
    add_to_path = path_to_wit / 'staging_area' / relative_to_wit
    if add_obj_path.is_file(): 
        if not add_to_path.parent.exists():
            os.makedir(add_to_path.parent)
        shutil.copy2(add_obj_path.resolve(), add_to_path.parent)
    elif add_obj_path.is_dir():
        if not add_to_path.exists():
            shutil.copytree(add_obj_path.resolve(), add_to_path)
#----------------------------------------------
#----------COMMIT FUNCTION---------------------
#----------------------------------------------      
def commit(msg, sec_parent=None):
    path_to_wit = check_wit_init()[0]
    refer = path_to_wit / 'references.txt'
    staging_path = path_to_wit / 'staging_area'
    with open(str(path_to_wit / 'activated.txt') , 'r') as active:
        active_branch = active.readline().strip()
    if refer.exists():
        with open(str(refer), 'r') as ref:
            ref_lines = []
            head_id = ref.readline().split('=')[1].strip()
            master_id = ref.readline().split('=')[1].strip()
            ref_lines.append(f'HEAD={head_id}\n')
            ref_lines.append(f'master={master_id}\n')
            lines = ref.readlines()
            ref_lines.extend(lines)
        path_old_commit = path_to_wit / 'images' / head_id
        if not compare_dics(staging_path, path_old_commit) and not compare_dics(path_old_commit, staging_path):
            print('Nothing has changed since last commit!')
            sys.exit()
    else:   
        head_id = 'None'
    message = msg
    commit_id = ''
    for i in range(40):
        commit_id += random.choice('0123456789abcdef')
    path_to_new_commit = path_to_wit / 'images' / commit_id
    with open(str(path_to_new_commit) + '.txt', 'w') as commit_metadata:
        if sec_parent:
            commit_metadata.write(f'parents={head_id},{sec_parent}\n')
        else:
            commit_metadata.write(f'parent = {head_id}\n')
        date_string = datetime.datetime.now().ctime()
        commit_metadata.write('date= ' + date_string + f'\nmessage={message}')
    shutil.copytree(staging_path, path_to_new_commit)
    if refer.exists():
        new_ref_lines = []   
        for line in ref_lines:
            name = line.split('=')[0].strip()
            name_id =line.split('=')[1].strip()
            if name == active_branch or name == 'HEAD':
                name_id = commit_id
            new_ref_lines.append(f'{name}={name_id}\n')
        with open(str(path_to_wit) + '\\references.txt', 'w') as ref:
            for line in new_ref_lines:
                ref.write(line)
    else:
        with open(str(path_to_wit) + '\\references.txt', 'w') as ref:
            ref.write(f'HEAD={commit_id}\nmaster={commit_id}\n')
    print(f'new commit: {commit_id} created!')
#----------------------------------------------
#----------STATUS FUNCTION---------------------
#----------------------------------------------
def status(checkout=False):
    path_to_wit, cwd_path = check_wit_init()
    path_to_staging = path_to_wit / 'staging_area'
    if (path_to_wit / 'references.txt').exists():
        with open(str(path_to_wit) + '\\references.txt', 'r') as ref:
            head_id = ref.readline().split('=')[1].strip()
        last_commit_dir = path_to_wit / 'images' / head_id
        changes_to_be_committed = compare_dics(path_to_staging, last_commit_dir)
    else:
        changes_to_be_committed = []
    not_staged = compare_dics(path_to_staging, cwd_path.resolve())
    root_staging = dircmp(cwd_path.resolve(), path_to_staging).left_only
    untracked_files = [(cwd_path.resolve() / name) for name in root_staging]
    if checkout:
        return (changes_to_be_committed, not_staged, untracked_files)
    print(f'WIT STATUS MESSAGE:')
    print('-' * 30)
    print('Changes to be committed:')
    for name in changes_to_be_committed:
        print(name)
    print('-' * 30)
    print('Changes not staged for commit:')
    for name in not_staged:
        print(name)
    print('-' * 30)
    print('Untracked files:')
    for name in untracked_files:
        print(name)
#----------------------------------------------
#------------REMOVE FUNCTION-------------------
#----------------------------------------------
def rm(rm_obj):
    path_to_wit = check_wit_init()[0]   
    p = Path(rm_obj)
    path_to_wit = get_wit_path(p.resolve())
    if p.resolve() == Path(os.getcwd()).resolve():
        staging = path_to_wit / 'staging_area'
        for sub in staging.iterdir():
            if sub.is_dir():
                shutil.rmtree(sub)
            else:
                sub.unlink()
        sys.exit()
    staging = path_to_wit / 'staging_area'
    rm_obj_path = staging / rm_obj
    for sub in staging.iterdir():
        if sub == rm_obj_path.resolve():
            print(rm_obj_path, sub)
            if sub.is_dir():
                shutil.rmtree(sub)
            else:
                sub.unlink()
#----------------------------------------------
#------------CHECKOUT FUNCTION-----------------
#----------------------------------------------
def checkout(commit_id):
    # check if checkout can go on its way using status- if there's changes_to_be_commited or not_staged then you cant checkout
    changes_to_be_commited, not_staged, untracked_files = status(checkout=True)
    if changes_to_be_commited or not_staged:
        print(f'you still have changes to be committed or changes not staged for commmit:{changes_to_be_commited, not_staged}')
        sys.exit()
    cwd_path = Path(os.getcwd()).resolve()
    path_to_wit = get_wit_path(cwd_path)
    with open(path_to_wit / 'references.txt', 'r') as ref:
        ref_lines = ref.readlines()
        branch = None
    for line in ref_lines:
        if commit_id == line.split('=')[0].strip():
            branch = commit_id
            print(branch)
            commit_id = line.split('=')[1].strip()
            print(f'branch:{branch}')
    if branch is not None:
        with open(path_to_wit / 'activated.txt' ,'w') as active:
            active.write(branch)
    # delete the root dir to get it ready for importing the commit_id dir, without touching the untracking files
    for sub in cwd_path.iterdir():
        if sub not in untracked_files:
            if sub.is_dir():
                shutil.rmtree(sub)
            else:
                sub.unlink() 
     # copy the commit_id dir to root
    commit_path = path_to_wit / 'images' / commit_id
    if not commit_path.exists():
        print(f'invalid commit_id {commit_id}')
        sys.exit()
    print(f'checkout to: {commit_id}')
    untracked_names = [name.relative_to(cwd_path) for name in untracked_files]
    for sub in commit_path.iterdir():
        if sub.relative_to(commit_path) not in untracked_names:
            if sub.is_dir():
                shutil.copytree(sub, cwd_path / sub.relative_to(commit_path))
            else:
                shutil.copy2(sub, cwd_path)
    #  copy commit_id dir  to staging
    staging = path_to_wit / 'staging_area'
    remove_staging_cont(staging, include=True)
    shutil.copytree(commit_path, staging)
    # change HEAD in ref file
    new_head_line = f'HEAD={commit_id}\n'

    ref_lines[0] = new_head_line
    
    with open(str(path_to_wit) + '\\references.txt', 'w') as ref:
        for line in ref_lines:
            ref.write(line)
#----------------------------------------------
#------------GRAPH FUNCTION--------------------
#----------------------------------------------
def get_parent(wit_path, current):
    '''
    '''
    if current == 'None':
        return None
    path_to_head_meta = wit_path / 'images' / (current + '.txt')
    with open(str(path_to_head_meta), 'r') as head_meta:
        par_id = head_meta.readline().split('=')[1].strip()
    return par_id

def graph(all=False):
    commits = []
    wit_path, cwd_path = check_wit_init()
    ref_file_path = wit_path / 'references.txt'
    if not ref_file_path.exists():
        print('no commit created yet')
        sys.exit()
    with open(str(ref_file_path), 'r') as ref:
        current = ref.readline().split('=')[1].strip()
    while current != 'None':
        commits.append(current)
        current = get_parent(wit_path, current)
    g = Digraph(comment='wit graph', format='png', node_attr={'color': 'lightblue2', 'style': 'filled'})
    length = len(commits)
    for i, commit in enumerate(commits):
        g.node(str(i), (commit[:20] +'\n' + commit[20:]))
        if (i + 1) < length:
            g.edge(str(i), str(i+1))
    g.edge('HEAD', '0')
    g.view()
#----------------------------------------------
#------------BRANCH FUNCTION-------------------
#----------------------------------------------
def branch(branch_name):
    path_to_wit, cwd_path = check_wit_init()
    reference = path_to_wit / 'references.txt'
    if not reference.exists():
        print('no commit has been created yet!')
        sys.exit()
    with open(str(reference), 'r') as ref:
        head = ref.readline().split('=')[1].strip()
        
    with open(str(reference), 'a') as ref:
        ref.write(f'{branch_name}={head}\n')

    print(f'new branch: {branch_name} created!')
#----------------------------------------------
#------------MERGE FUNCTION--------------------
#----------------------------------------------
def get_common_parent(list_a, list_b):
    for parent_a in list_a:
        for parent_b in list_b:
            if parent_a == parent_b:
                return parent_a
    return None

def get_all_parents(path_to_wit, child):
    parents_of = []
    while child != 'None':
        parents_of.append(child)
        child = get_parent(path_to_wit, child)
    print('*'*50 + f'\nparents={parents_of}')
    return parents_of

def get_branch_id(refer_path, branch_name):
    with open(str(refer_path), 'r') as refer_file:
        head_id = refer_file.readline().split('=')[1].strip()
        if branch_name == 'HEAD':
            return head_id
        refer_lines = refer_file.readlines()
    for line in refer_lines:
        name = line.split('=')[0].strip()
        name_id = line.split('=')[1].strip()
        if name == branch_name:
            branch_id = name_id
            return branch_id

def merge(branch_to_merge):
    path_to_wit, cwd_path = check_wit_init()
    refer_path = path_to_wit / 'references.txt'
    branch_id = get_branch_id(refer_path, branch_to_merge)
    head_id = get_branch_id(refer_path, 'HEAD')
    print(f'HEAD={head_id} \nbranch to merge={branch_id}\n{branch_to_merge}')
    # get parents of both HEAD and branch_to_merge and find closest common parent
    parents_of_head = get_all_parents(path_to_wit, head_id)
    parents_of_branch = get_all_parents(path_to_wit, branch_id)
    common_parent = get_common_parent(parents_of_head, parents_of_branch)
    print(common_parent)
# find all file that changed from common parent to branch_to_merge
    common_parent_path = path_to_wit / 'images' / common_parent
    branch_path = path_to_wit / 'images' / branch_id
    head_path = path_to_wit / 'images' / head_id
    changes1 = compare_dics(branch_path, common_parent_path)
    for change in changes1:
        change = Path(change)
        if change.is_file():
            print('file')
            shutil.copy2(change, (path_to_wit / 'staging_area'))
        if change.is_dir():
            print('dir')
            path_to_copy = path_to_wit / 'staging_area' / change.relative_to(change.parent)
            if not path_to_copy.exists():
                shutil.copytree(change, path_to_copy)
            else:
                print('asd')
    commit('merge_try', sec_parent=branch_id)           
        
# replace these files in staging
# commit

#----------------------------------------------
#------------MAIN FUNCTION---------------------
#----------------------------------------------
def main():
    usage = "Usage : <Path / to / wit> <command> <args>"
    if len(sys.argv) < 2:
        print(usage)
        sys.exit()
    if sys.argv[1] == 'init':
        init()
    elif sys.argv[1] == 'add':
        if len(sys.argv) < 3:
            print("File or Directory to add not given\n" + usage)
            sys.exit()
        add(sys.argv[2])
    elif sys.argv[1] == 'commit':
        if len(sys.argv) < 3:
            print("Message for commit not given\n" + usage)
            sys.exit()
        commit(sys.argv)
    elif sys.argv[1] == 'status':
        status()
    elif sys.argv[1] == 'rm':
        if len(sys.argv) < 3:
            print("File or Directory to remove not given\n" + usage)
            sys.exit()
        rm(sys.argv[2])
    elif sys.argv[1] == 'checkout':
        if len(sys.argv) < 3:
            print("Directory to replace not given\n" + usage)
            sys.exit()
        checkout(sys.argv[2])
    elif sys.argv[1] == 'graph':
        graph()
    elif sys.argv[1] == 'branch':
        if len(sys.argv) < 3:
            print("Name of branch not given\n" + usage)
            sys.exit()
        branch(sys.argv[2])
    elif sys.argv[1] == 'merge':
        if len(sys.argv) < 3:
            print("Name of branch to merge with not given\n" + usage)
            sys.exit()
        merge(sys.argv[2])
    else:
        print(usage)
        sys.exit()
if __name__ == "__main__":
    main()

