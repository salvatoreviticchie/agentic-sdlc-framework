"""Unit tests for todo.py. Run: python3 -m unittest -v (from this folder)."""

import os
import tempfile
import unittest

import todo


class TodoListTest(unittest.TestCase):

    def test_add_returns_the_task_number(self):
        t = todo.TodoList()
        self.assertEqual(t.add("Buy milk"), 1)
        self.assertEqual(t.add("Call Sam"), 2)

    def test_add_refuses_an_empty_title(self):
        with self.assertRaises(ValueError):
            todo.TodoList().add("   ")

    def test_complete_marks_the_task_done(self):
        t = todo.TodoList()
        t.add("Buy milk")
        t.add("Call Sam")
        self.assertEqual(t.complete(2), "Call Sam")
        self.assertEqual(t.open_tasks(), [(1, "Buy milk")])

    def test_clear_done_removes_only_finished_tasks(self):
        t = todo.TodoList()
        t.add("Buy milk")
        t.add("Call Sam")
        t.complete(1)
        self.assertEqual(t.clear_done(), 1)
        self.assertEqual(t.open_tasks(), [(1, "Call Sam")])


class StorageTest(unittest.TestCase):

    def test_save_then_load_keeps_the_tasks(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "todo.json")
            t = todo.TodoList()
            t.add("Buy milk")
            todo.save(t, path)
            self.assertEqual(todo.load(path).open_tasks(), [(1, "Buy milk")])

    def test_load_of_a_missing_file_is_an_empty_list(self):
        self.assertEqual(todo.load("/no/such/file.json").tasks, [])


if __name__ == "__main__":
    unittest.main()
