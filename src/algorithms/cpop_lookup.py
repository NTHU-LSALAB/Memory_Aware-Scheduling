from heapq import heapify, heappop, heappush
from algorithms.algo_base import AlgoBase
from algorithms.cpop import calculate_priority, find_critical_processor, find_processor, set_critical_node
from platforms.memory import Memory
from platforms.task import Task


class CPOPLookup(AlgoBase):

    def schedule(self, tasks: list[Task], input, options: dict) -> tuple[list[list[Task]], int]:
        # print('lookup version')
        self.options = options
        self.input = input
        self.reserved_list = []
        self.makespan = 0
        entry_task = next(
            (task for task in tasks if task.is_entry()), None)
        exit_task = next(
            (task for task in tasks if task.is_exit()), None)

        if entry_task is None or exit_task is None:
            raise ValueError('No entry or exit node')

        # calculate priority
        calculate_priority(entry_task, exit_task)
        for task in tasks:
            task.priority = task.rank_upward + task.rank_downward
        set_critical_node(entry_task)
        self.critical_procId = find_critical_processor(entry_task)

        self.schedule: list[list[Task]] = [[]
                                           for _ in range(len(entry_task.cost_table))]

        self.task_heap = [entry_task]
        heapify(self.task_heap)

        # for rollback
        while len(self.task_heap):
            task = heappop(self.task_heap)
            self.rollback_list = []
            success = self.reserve(task, options.get('depth', 1))
            if not success:
                self.rollback(task)

            # update heap
            for out_edge in task.out_edges:
                heappush(self.task_heap, out_edge.target)
                    
        if exit_task.procId == None:
            raise ValueError('Fail to allocate memory')
        if options.get('plot', True):
            suffix = options.get('suffix', '')
            self.memory.plot(
                self.makespan, filename=f'cpop-lookup{suffix}')
            self.plot(self.schedule, self.makespan, f'cpop-lookup{suffix}')
        return self.schedule, self.makespan, self.memory.max()

    def reserve(self, task: Task, depth=1):
        return self.__reserve_re(task, depth)

    def __reserve_re(self, task: Task, depth):
        if depth == -1:
            return True

        can_reserve = self.allocate_dependencies(task)

        # reserve for children
        for edge in task.out_edges:
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
        est, eft, pid = find_processor(task, self.schedule, self.critical_procId)
        ################################ Allocate memory ################################
        checked = True  # Accumulate checked
        latest_start = est  # AST
        mode = self.options.get('strategy', 'best')
        # Allocate input tensor

        if task.is_entry():
            ok, slot = self.memory.fit(
                self.input, [est, eft], task, mode=mode)
            if slot:
                latest_start = max(latest_start, slot.interval[0])
            checked = checked and ok

        # Allocate a task's output tensor
        ok, slot = self.memory.fit(task.output, [
            est, eft if task.is_exit() else Memory.DEADLINE], task, final=False, mode=mode)
        if slot:
            latest_start = max(latest_start, slot.interval[0])
        checked = checked and ok

        # Allocate internal buffer
        ok, slot = self.memory.fit(
            task.buffer_size, [latest_start, latest_start + eft - est], task, mode=mode)
        if slot:
            latest_start = max(latest_start, slot.interval[0])
        checked = checked and ok

        # Now we know the ast, aft
        ast = latest_start
        aft = latest_start + eft - est

        if checked:
            # Free input tensors
            if not task.is_entry():
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
                        self.memory.free_tensor(in_edge.source, until)

            self.reserved_list.append(task)
            task.procId = pid + 1
            task.ast = ast
            task.aft = aft

            self.schedule[pid].append(task)
            # update makespan
            if task.aft > self.makespan:
                self.makespan = task.aft
        return checked

    def rollback(self, task, depth=1):
        if depth == -1:
            return True

        for task in self.rollback_list:
            # reset task value
            task.rollback()
            # remove from reserve list
            if task in self.reserved_list:
                self.reserved_list.remove(task)
            # remove memory allocation
            self.memory.rollback(task.id)
            # remove from memory
            for proc_schedule in self.schedule:
                for t in proc_schedule:
                    if t.id == task.id:
                        proc_schedule.remove(t)
            # remove successors from ready q
            # for out_edge in task.out_edges:
            #     if out_edge.target in self.task_heap:
            #         self.task_heap.remove(out_edge.target)

    def allocate_dependencies(self, task: Task):
        checked = True
        for edge in task.in_edges:
            checked = checked and self.allocate_dependencies(edge.source)
        return checked and self.allocate_memory(task)

    def print_priority(self, entry_task: Task):
        print('''UPPER RANKS
---------------------------
Task    Rank
---------------------------''')
        self.bfs(entry_task, op=lambda task: print(
            f'{task.id}       {round(task.priority, 4)}'))
