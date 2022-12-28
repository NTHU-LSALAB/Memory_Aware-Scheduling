from functools import cmp_to_key
from heapq import heapify, heappop, heappush
from algorithms.sbac import adjust_priority
from lib.utils import ssse
from platforms.memory import Memory
from platforms.task import Task
from inspect import signature


def base(cls):
    class Wrapped(cls):
        def schedule(self, tasks: list[Task], input, options={}, format='default') -> tuple[list[list[Task]], int]:
            # print('Base')
            makespan = 0
            task_count = len(
                list(filter(lambda task: isinstance(task, Task), tasks)))
            entry_task, exit_task = ssse(tasks)
            self.tasks = tasks

            args = (entry_task, )
            if len(signature(self.calculate_priority).parameters) == 2:
                args = args + (exit_task, )
            self.calculate_priority(*args)

            schedule: list[list[Task]] = [[]
                                          for _ in range(len(entry_task.cost_table))]

            task_heap = [entry_task]
            heapify(task_heap)

            while len(task_heap):
                task = heappop(task_heap)

                if isinstance(task, Task):
                    if task.procId is not None:
                        continue
                    est, eft, pid = self.find_processor(task, schedule)
                    latest_start = est  # AST

                    if format == 'default':
                        # allocate input tensor
                        if task is entry_task:
                            self.memory.fit(
                                input, [est, eft], task, can_delay=False)
                        # allocate output tensor
                        self.memory.fit(task.output, [
                            est, eft if task.is_exit() else Memory.DEADLINE], task, final=False, can_delay=False)

                        self.memory.fit(
                            task.buffer_size, [latest_start, latest_start + eft - est], task, can_delay=False)
                    else:
                        # allocate memory
                        for m_edge in task.m_in_edges:
                            if m_edge.source.type == 'allocate':
                                ok, _ = self.memory.fit(m_edge.source.buffer, [
                                    est, eft if task.id == task_count else Memory.DEADLINE], m_edge.source, final=False)
                                if not ok:
                                    raise ValueError('Fail to allocate memory')

                    ast = latest_start
                    aft = latest_start + eft - est

                    task.procId = pid + 1
                    task.ast = ast
                    task.aft = aft
                    schedule[pid].append(task)

                    if format == 'default':
                        # free input tensors
                        if task is not entry_task:
                            # check if inputs can be free
                            for in_edge in task.in_edges:
                                last_use = True
                                until = -1
                                for out_edge in in_edge.source.out_edges:
                                    if out_edge.target is task:
                                        continue
                                    if out_edge.target.procId is None:  # not allocate yet
                                        last_use = False
                                        break
                                    until = max(until, out_edge.target.aft)
                                if last_use:
                                    until = max(until, aft)
                                    self.memory.free_tensor(
                                        in_edge.source, until)
                    else:
                        # free tensors
                        for m_edge in task.m_out_edges:
                            if m_edge.target.type == 'free':
                                last_use = True
                                until = -1
                                for in_edge in m_edge.target.t_in_edges:
                                    if in_edge.source.procId is None:
                                        last_use = False
                                        break
                                    until = max(until, in_edge.source.aft)
                                if last_use:
                                    until = max(until, aft)
                                    self.memory.free_tensor(
                                        m_edge.target, until)

                    if task.aft > makespan:
                        makespan = task.aft

                # update heap
                for out_edge in task.out_edges:
                    last_use = True
                    for in_edge in out_edge.target.t_in_edges:
                        if in_edge.source.procId is None:
                            last_use = False
                    if last_use:
                        heappush(task_heap, out_edge.target)

            if options.get('plot', True):
                suffix = options.get('suffix', '')
                self.memory.plot(
                    makespan, filename=f'heft-base{suffix}')
                self.plot(schedule, makespan, f'heft-base{suffix}')
            return schedule, makespan, self.memory.max()

    return Wrapped


def delay(cls):
    class Wrapped(cls):
        def schedule(self, tasks: list[Task], input, options={}, format='default') -> tuple[list[list[Task]], int]:
            # print('delay')
            makespan = 0
            task_count = len(
                list(filter(lambda task: isinstance(task, Task), tasks)))
            entry_task, exit_task = ssse(tasks)
            self.tasks = tasks

            args = (entry_task, )
            if len(signature(self.calculate_priority).parameters) == 2:
                args = args + (exit_task, )
            self.calculate_priority(*args)

            schedule: list[list[Task]] = [[]
                                          for _ in range(len(entry_task.cost_table))]

            task_heap = [entry_task]
            heapify(task_heap)

            while len(task_heap):
                task = heappop(task_heap)

                if isinstance(task, Task):
                    if task.procId is not None:
                        continue
                    # print('==============',task.id, '=============')
                    est, eft, pid = self.find_processor(task, schedule)
                    latest_start = est  # AST

                    if format == 'default':
                        # allocate input tensor
                        if task is entry_task:
                            _, slot = self.memory.fit(
                                input, [est, eft], task)
                            if slot:
                                latest_start = max(
                                    latest_start, slot.interval[0])
                        # allocate output tensor
                        ok, slot = self.memory.fit(task.output, [
                            est, eft if task.is_exit() else Memory.DEADLINE], task, final=False)
                        if not ok:
                            raise ValueError('Fail to allocate memory')
                        if slot:
                            latest_start = max(latest_start, slot.interval[0])

                        ok, slot = self.memory.fit(
                            task.buffer_size, [latest_start, latest_start + eft - est], task)
                        if not ok:
                            raise ValueError('Fail to allocate memory')
                        if slot:
                            latest_start = max(latest_start, slot.interval[0])
                    else:
                        # allocate memory
                        for m_edge in task.m_in_edges:
                            if m_edge.source.type == 'allocate':
                                ok, slot = self.memory.fit(m_edge.source.buffer, [
                                    est, eft if task.id == task_count else Memory.DEADLINE], m_edge.source, final=False)
                                if not ok:
                                    raise ValueError('Fail to allocate memory')
                                if slot:
                                    latest_start = max(
                                        latest_start, slot.interval[0])

                    ast = latest_start
                    aft = latest_start + eft - est

                    task.procId = pid + 1
                    task.ast = ast
                    task.aft = aft
                    schedule[pid].append(task)

                    if format == 'default' and task.id != 0:
                        # free input tensors
                        if task is not entry_task:
                            # check if inputs can be free
                            for in_edge in task.in_edges:
                                last_use = True
                                until = -1
                                for out_edge in in_edge.source.out_edges:
                                    if out_edge.target is task:
                                        continue
                                    if out_edge.target.procId is None:  # not allocate yet
                                        last_use = False
                                        break
                                    until = max(until, out_edge.target.aft)
                                if last_use:
                                    until = max(until, aft)
                                    self.memory.free_tensor(
                                        in_edge.source, until)
                    elif task.id != 0:
                        # free tensors
                        # print(f'======== {task.id} ========')
                        for m_edge in task.m_out_edges:
                            if m_edge.target.type == 'free':
                                last_use = True
                                until = -1
                                # print(m_edge.target.id)
                                for in_edge in m_edge.target.t_in_edges:
                                    if in_edge.source.procId is None:
                                        last_use = False
                                        break
                                    until = max(until, in_edge.source.aft)
                                if last_use:
                                    # print(task.id, 'free', 'mId:', m_edge.target.mId)
                                    until = max(until, aft)
                                    self.memory.free_tensor(
                                        m_edge.target, until)

                    if task.aft > makespan:
                        makespan = task.aft

                # update heap
                for out_edge in task.out_edges:
                    last_use = True
                    for in_edge in out_edge.target.t_in_edges:
                        if in_edge.source.procId is None:
                            last_use = False
                    if last_use:
                        heappush(task_heap, out_edge.target)

            if options.get('plot', True):
                suffix = options.get('suffix', '')
                self.memory.plot(
                    makespan, filename=f'heft-delay{suffix}')
                if options.get('snapshot'):
                    self.memory.plot_snapshot(
                        makespan, filename=f'heft-delay{suffix}')
                self.plot(schedule, makespan, f'heft-delay{suffix}')
            return schedule, makespan, self.memory.max()
    return Wrapped


def reserve(cls):
    class Wrapped(cls):
        def __init__(self):
            pass

        def schedule(self, tasks: list[Task], input, options: dict = {}, format='default') -> tuple[list[list[Task]], int]:
            self.format = format
            # print('reserve version')
            self.options = options
            self.input = input
            self.reserved_list = []
            self.makespan = 0

            self.task_count = len(
                list(filter(lambda task: isinstance(task, Task), tasks)))
            entry_task, exit_task = ssse(tasks)
            self.tasks = tasks

            args = (entry_task, )
            if len(signature(self.calculate_priority).parameters) == 2:
                args = args + (exit_task, )
            # calculate priority
            self.calculate_priority(*args)

            self.schedule: list[list[Task]] = [[]
                                               for _ in range(len(entry_task.cost_table))]

            self.task_heap = [entry_task]
            heapify(self.task_heap)

            # for rollback
            while len(self.task_heap):
                task = heappop(self.task_heap)
                self.rollback_list = []
                if isinstance(task, Task) and task not in self.reserved_list:
                    # print('============', task.id, '==============')
                    success = self.reserve(task, options.get('depth', 1))
                    # print('success:', success)
                    # print(list(map(lambda task: task.id, self.reserved_list)))
                    if not success:
                        self.rollback(task)

                # update heap
                for out_edge in task.out_edges:
                    if out_edge.target not in self.task_heap:
                        heappush(self.task_heap, out_edge.target)
            if len(list(filter(lambda task: isinstance(task, Task)
                               and task.procId == None, tasks))):
                raise ValueError('Fail to allocate memory')
            if options.get('plot', True):
                suffix = options.get('suffix', '')
                self.memory.plot(
                    self.makespan, filename=f'heft-reserve{suffix}')
                if options.get('snapshot'):
                    self.memory.plot_snapshot(
                        self.makespan, filename=f'heft-reserve{suffix}')
                self.plot(self.schedule, self.makespan,
                          f'heft-reserve{suffix}')
            return self.schedule, self.makespan, self.memory.max()

        def reserve(self, task: Task, depth=1):
            return self.__reserve_re(task, depth)

        def __collect_tasks(self, task: Task, depth=1):
            if depth == -1:
                return []

            tasks = [task]

            # reserve for children
            for edge in task.t_out_edges:
                tasks.extend(self.__collect_tasks(
                    edge.target, depth-1))

            return tasks

        def __reserve_re(self, task: Task, depth):
            if depth == -1:
                return True

            can_reserve = self.allocate_dependencies(task)

            # reserve for children
            for edge in task.t_out_edges:
                can_reserve = can_reserve and self.__reserve_re(
                    edge.target, depth-1)

            return can_reserve

        def allocate_memory(self, task: Task):
            # Already allocated
            if task in self.reserved_list:
                return True
            # For rollback
            if task not in self.rollback_list:
                self.rollback_list.append(task)

            ####################### Schedule the task on a proccessor #######################
            est, eft, pid = self.find_processor(
                task, self.schedule)
            ################################ Allocate memory ################################
            checked = True  # Accumulate checked
            latest_start = est  # AST
            # Allocate input tensor
            if self.format == 'default':
                if task.is_entry():
                    ok, slot = self.memory.fit(
                        self.input, [est, eft], task)
                    if slot:
                        latest_start = max(latest_start, slot.interval[0])
                    checked = checked and ok

                # Allocate a task's output tensor
                ok, slot = self.memory.fit(task.output, [
                    est, eft if task.is_exit() else Memory.DEADLINE], task, final=False)
                if slot:
                    latest_start = max(latest_start, slot.interval[0])
                checked = checked and ok

                # Allocate internal buffer
                ok, slot = self.memory.fit(
                    task.buffer_size, [latest_start, latest_start + eft - est], task)
                if slot:
                    latest_start = max(latest_start, slot.interval[0])
                checked = checked and ok
            else:
                # allocate memory
                for m_edge in task.m_in_edges:
                    if m_edge.source.type == 'allocate':
                        ok, slot = self.memory.fit(m_edge.source.buffer, [
                            est, eft if task.id == self.task_count else Memory.DEADLINE], m_edge.source, final=False)
                        if slot:
                            latest_start = max(
                                latest_start, slot.interval[0])
                        checked = checked and ok

            # Now we know the ast, aft
            ast = latest_start
            aft = latest_start + eft - est

            if checked:

                self.reserved_list.append(task)
                task.procId = pid + 1
                task.ast = ast
                task.aft = aft

                if self.format == 'default':
                    # Free input tensors
                    if not task.is_entry():
                        # check if inputs can be free
                        for in_edge in task.t_in_edges:
                            # if task.id == 15:
                            #     print('parent:', in_edge.source.id)
                            last_use = True
                            until = -1
                            # if task.id == 15:
                            #     print('siblings:')
                            for out_edge in in_edge.source.t_out_edges:
                                # if task.id == 15:
                                #     print(out_edge.target.id)
                                if out_edge.target is task:
                                    continue
                                if out_edge.target.procId is None:  # not allocate yet
                                    last_use = False
                                    break
                                until = max(until, out_edge.target.aft)
                            if last_use:
                                until = max(until, aft)
                                self.memory.free_tensor(
                                    in_edge.source, until)
                else:
                    # free tensors
                    for m_edge in task.m_out_edges:
                        if m_edge.target.type == 'free':
                            last_use = True
                            until = -1
                            for in_edge in m_edge.target.t_in_edges:
                                if in_edge.source.procId is None:
                                    last_use = False
                                    break
                                until = max(until, in_edge.source.aft)
                            if last_use:
                                until = max(until, aft)
                                self.memory.free_tensor(
                                    m_edge.target, until)

                self.schedule[pid].append(task)
                # update makespan
                if task.aft > self.makespan:
                    self.makespan = task.aft
            return checked

        def rollback(self, task, depth=1):
            if depth == -1:
                return True

            # print('Rollback:', list(map(lambda task: task.id, self.rollback_list)))
            for t in self.rollback_list:
                # reset task value
                t.rollback()
                # remove from reserve list
                if t in self.reserved_list:
                    self.reserved_list.remove(t)
                if self.format == 'default':
                    # remove memory allocation
                    self.memory.rollback(t.id)
                else:
                    for m_edge in t.m_in_edges:
                        self.memory.rollback(m_edge.source.id)
                # remove from memory
                for proc_schedule in self.schedule:
                    for slot in proc_schedule:
                        if t.id == slot.id:
                            proc_schedule.remove(t)
                # remove successors from ready q
                # for out_edge in task.out_edges:
                #     if out_edge.target in self.task_heap:
                #         self.task_heap.remove(out_edge.target)

        def allocate_dependencies(self, task: Task):
            checked = True

            def edge_compare(edge1, edge2):
                task1 = edge1.source
                task2 = edge2.source
                if task1.priority == task2.priority:
                    return task1.id > task2.id
                else:
                    return task1.priority > task2.priority
            # print('current:', task.id)
            for edge in sorted(task.t_in_edges, key=cmp_to_key(edge_compare)):
                # print(edge.source.priority)
                checked = checked and self.allocate_dependencies(
                    edge.source)
            return checked and self.allocate_memory(task)
    return Wrapped


def sbac(cls):

    class Wrapped(cls):
        def schedule(self, tasks: list[Task], input, options={}, format='default') -> tuple[list[list[Task]], int]:
            # print('SBAC')
            makespan = 0
            entry_task, exit_task = ssse(tasks)
            self.tasks = tasks

            args = (entry_task, )
            if len(signature(self.calculate_priority).parameters) == 2:
                args = args + (exit_task, )
            self.calculate_priority(*args)
            adjust_priority(tasks)

            schedule: list[list[Task]] = [[]
                                          for _ in range(len(entry_task.cost_table))]

            task_heap = [entry_task]
            heapify(task_heap)

            while len(task_heap):
                task = heappop(task_heap)

                if isinstance(task, Task):
                    if task.procId is not None:
                        continue
                    est, eft, pid = self.find_processor(task, schedule)
                    latest_start = est  # AST

                    if format == 'default':
                        # allocate input tensor
                        if task is entry_task:
                            _, slot = self.memory.fit(
                                input, [est, eft], task)
                            if slot:
                                latest_start = max(
                                    latest_start, slot.interval[0])
                        # allocate output tensor
                        ok, slot = self.memory.fit(task.output, [
                            est, eft if task.is_exit() else Memory.DEADLINE], task, final=False)
                        if not ok:
                            raise ValueError('Fail to allocate memory')
                        if slot:
                            latest_start = max(latest_start, slot.interval[0])

                        ok, slot = self.memory.fit(
                            task.buffer_size, [latest_start, latest_start + eft - est], task)
                        if not ok:
                            raise ValueError('Fail to allocate memory')
                        if slot:
                            latest_start = max(latest_start, slot.interval[0])
                    else:
                        # allocate memory
                        for m_edge in task.m_in_edges:
                            if m_edge.source.type == 'allocate':
                                ok, slot = self.memory.fit(m_edge.source.buffer, [
                                    est,  Memory.DEADLINE], m_edge.source, final=False)
                                if not ok:
                                    raise ValueError('Fail to allocate memory')
                                if slot:
                                    latest_start = max(
                                        latest_start, slot.interval[0])

                    ast = latest_start
                    aft = latest_start + eft - est

                    task.procId = pid + 1
                    task.ast = ast
                    task.aft = aft
                    schedule[pid].append(task)

                    if format == 'default':
                        # free input tensors
                        if task is not entry_task:
                            # check if inputs can be free
                            for in_edge in task.in_edges:
                                last_use = True
                                until = -1
                                for out_edge in in_edge.source.out_edges:
                                    if out_edge.target is task:
                                        continue
                                    if out_edge.target.procId is None:  # not allocate yet
                                        last_use = False
                                        break
                                    until = max(until, out_edge.target.aft)
                                if last_use:
                                    until = max(until, aft)
                                    self.memory.free_tensor(
                                        in_edge.source, until)
                    else:
                        # free tensors
                        for m_edge in task.m_out_edges:
                            if m_edge.target.type == 'free':
                                last_use = True
                                until = -1
                                for in_edge in m_edge.target.t_in_edges:
                                    if in_edge.source.procId is None:
                                        last_use = False
                                        break
                                    until = max(until, in_edge.source.aft)
                                if last_use:
                                    until = max(until, aft)
                                    self.memory.free_tensor(
                                        m_edge.target, until)

                    if task.aft > makespan:
                        makespan = task.aft

                # update heap
                for out_edge in task.out_edges:
                    last_use = True
                    for in_edge in out_edge.target.t_in_edges:
                        if in_edge.source.procId is None:
                            last_use = False
                    if last_use:
                        heappush(task_heap, out_edge.target)

            if options.get('plot', True):
                suffix = options.get('suffix', '')
                self.memory.plot(
                    makespan, filename=f'heft-sbac{suffix}')
                self.plot(schedule, makespan, f'heft-sbac{suffix}')
            return schedule, makespan, self.memory.max()

    return Wrapped
