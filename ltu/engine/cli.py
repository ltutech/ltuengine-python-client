#!/usr/bin/env python

import logging
from multiprocessing.dummy import Pool
import os
import time
import sys

import begin
import coloredlogs
from tqdm import tqdm

from client import QueryClient, ModifyClient
from ltu.engine.result import Result
from ltu.engine.stat import Stat

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

global stat
stat = Stat()

def print_stat(nb_threads):
    """ print all the statistics global and per action """
    stat.print_stat_global()
    logger.info("")
    stat.print_result_per_action(nb_threads)

def get_action_name_from_function(function):
    """return from a function (add_image, search_image, delete_image) the name of the action concerned
    """
    return function.__name__.split('_')[0]

def run_single_task(items):
    """Run given action for one file
    """
    in_file = items[0]["in"]
    action_function = items[1]
    action = get_action_name_from_function(items[1])
    out_file = ""

    if  action in items[0]:
        out_file = items[0][action]
    if out_file:
        #launch action
        try:
            result = action_function(in_file)
            logger.debug("Finish with status %s" %(result.status_code))
            if result.status_code < 0:
                logger.debug('An issue occuted with the file {}. Consult the json result. file'.format(in_file))
                stat.nb_errors[action] += 1
            else:
                stat.treated[action] += 1

        except Exception as e:
            logger.critical('An issue has occured. Could not perform the action {}. The process is stopped: {}'.format(action,e))
            sys.exit(-1)

        #save the result in a json file
        try:
            result.save_json(out_file)
        except Exception as e:
            logger.critical('Could not save the result for the action {}: {}'.format(action,e))
            sys.exit(-1)


def run_task_mono_thread(action_function, files, action_label, nb_threads=1, offset=0):
    """Run given action on every files, one at a time.
    """
    items = ()
    for file in files[offset:]:
        items = (file,action_function)
        logger.info("")
        logger.info("%s: %s" % (action_label, file["in"]))
        run_single_task(items)


def run_task_multi_thread(action_function, files, action_label, nb_threads=2, offset=0):
    """Run given action on every files using a threading pool.
       It uses a progress bar instead of a usual verbose log.
    """
    pool = Pool(processes=nb_threads)
    items = [(file, action_function) for file in files[offset:]]
    pool_iterable = pool.imap_unordered(run_single_task, items)
    progress_bar_items = tqdm(total=len(items),
                              iterable=pool_iterable,
                              unit='images',
                              desc='{0: <30}'.format(action_label))
    for item in progress_bar_items:
        pass

def generate_actions_list_per_images(actions_list, input_dir, force):
    """Generate a list of actions to process per image. For each image are saved:
        - input path of the image
        - out path where save the result for each action to perform
    """
    # create results paths if they don't exist
    # result main repertory: out_result
    out_base_path = os.path.join(os.getcwd(), "out_result")
    if not os.path.exists(out_base_path):
        try:
            os.mkdir(out_base_path)
        except Exception as e:
            logger.critical('Could not create the out path "out_result": {}'.format(e))
            sys.exit(-1)

    #create one result folder per action
    for action in actions_list:
        action_path = os.path.join(out_base_path, action)
        if not os.path.exists(action_path):
            try:
                os.mkdir(action_path)

            except Exception as e:
                logger.critical('Could not create the action {} out path: {}'.format(e,action))
                sys.exit(-1)

    files = []
    b_file = False #indicate if there are files to performed
    untreated = 0

    image_path = os.path.basename(input_dir)

    for dirpath, _, fnames in os.walk(input_dir):
        #relative path from the input images folder, repertory per repertory
        relativ_path = os.path.relpath(dirpath,input_dir)

        if relativ_path == ".":
            relativ_path = ""

        #create actions repertories
        for action in actions_list:
            complete_path = os.path.join(out_base_path, action, image_path)
            if not os.path.exists(complete_path):
                try:
                    os.mkdir(complete_path)
                except Exception as e:
                    logger.critical('Could not create the out path {}: {}'.format(complete_path, e))
                    sys.exit(-1)

            complete_path = os.path.join(out_base_path, action, image_path, relativ_path)
            if not os.path.exists(complete_path):
                try:
                    os.mkdir(complete_path)
                except Exception as e:
                    logger.critical('Could not create the out path {}: {}'.format(complete_path, e))
                    sys.exit(-1)

        for file in fnames:
            # files_path["in"]: input image file path
            # files_path[action]: result json file path per action
            if not file == ".DS_Store": #Exept Mac store file
                b_file = True
                files_path = {}
                b_action = False
                for action in actions_list:
                    json_path = os.path.join(out_base_path, action, image_path,relativ_path, file) + ".json"
                    #if the folder don't exist or if the action is forced to be executed
                    #the imge will be processed
                    if not os.path.exists(json_path) or force:
                        b_action = True
                        stat.queries_to_treat += 1
                        files_path[action] = json_path
                    else:
                        #the image won't be performed
                        stat.already += 1
                        logger.debug("%s action already performed for this file. You can consult the result in the Json file. To generate new result, delete the Json File or force the %s action by adding the --force parameter in the command." %(action, action))

                if b_action:
                    files_path["in"] = os.path.join(dirpath, file)
                    files.append(files_path)

    #if no file to treat
    if not b_file and not files:
        assert files, "No input file found in %s" % input_dir
    elif b_file and not files:
        logger.info ("No new file to process. Delete old results folders or force the treatment by adding the --force parameter in the command.")

    return files

@begin.start
def ltuengine_process_dir(actions: "A list(separate each action by a comma) of actions to execute on a folder: add|delete|search or bench(that performs 'delete,add,search,delete') ",
                          application_key: "LTU Engine application key",
                          input_dir:"Folder with all needed inputs",
                          host:"server URL that hosts the application, default is LTU OnDemand"=None,
                          force:" a boolean to indicate what to do if a request has already been executed: force or not"=False,
                          nb_threads:"a list(separate each action by a comma) of number of threads"="1",
                          offset:"starting offset"=0):
    """
    Parse given directory for images and perform action [add|search|delete] on given LTU Engine
    application. Useful to add/delete a batch of images on multiple threads.

    """
    coloredlogs.install(level='info')
    ## process input parameters
    # get all actions
    if actions == "bench":
        actions = "delete,add,search,delete"
        force = True # for a bench actions are forced to be performed
    actions_list = actions.split(',')

    #verify if the action call is valid
    actions = ["add","search","delete"]
    for a in actions_list:
        if a not in actions:
            logger.error("Unknown action {}".format(a))
            sys.exit(-1)

    # get all threads nbr
    all_threads = nb_threads.split(',')
    for i in range(0, len(all_threads)):
        all_threads[i] = int(all_threads[i])
    # other parameters
    offset = int(offset)

    #lit of images to performed
    files = []
    #get input and output files path for each image
    files = generate_actions_list_per_images(actions_list, input_dir, force)

    if files:
        #nb images to treat
        nb_files = len(files) - offset
        stat.submitted += len(files)
        stat.to_treat += nb_files

        # create client
        logger.info("")
        modifyClient = ModifyClient(application_key, server_url=host)

        for nb_threads in all_threads:
            nb_errors_before_treatment = stat.nb_errors
            for action in actions_list:
                logger.info("")
                start_time = time.time()
                # get the appropriate function to run the task
                # - run_task_mono_thread will run on 1 thread and show some logs
                # - run_task_multi_thread will run on multiple threads and use a progress bar
                run_task = run_task_mono_thread if nb_threads == 1 else run_task_multi_thread
                # get the action to perform
                if action == actions[0]:
                    logger.info("Adding directory %s images into application %s" % (input_dir, application_key))
                    run_task(modifyClient.add_image, files, "Adding image", nb_threads, offset)
                elif action == actions[2]:
                    logger.info("Deleting directory %s images from application %s" % (input_dir, application_key))
                    run_task(modifyClient.delete_imagefile, files, "Deleting image", nb_threads, offset)
                elif action == actions[1]:
                    queryClient = QueryClient(application_key, server_url=host)
                    logger.info("Searching directory %s images into application %s" % (input_dir, application_key))
                    run_task(queryClient.search_image, files, "Searching image", nb_threads, offset)

                end_time = (time.time() - start_time)

                #save action statistics per
                stat.set_result_per_action(action, end_time)
                bench = "%s done, %d images, in %f sec on %d threads, %f images per sec" % (action, nb_files, end_time, nb_threads, nb_files/end_time)
                logger.debug(bench)

    print_stat(nb_threads)
