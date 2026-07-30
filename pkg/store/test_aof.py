import unittest
import os
from pkg.store.db import Database
from pkg.commands.handler import CommandHandler
from pkg.store.aof import AOFManager

class TestAOF(unittest.TestCase):
    def setUp(self):
        self.db = Database(run_cleaner=False)
        self.handler = CommandHandler(self.db)
        self.filepath = "test_appendonly.aof"
        if os.path.exists(self.filepath):
            os.remove(self.filepath)
        self.aof = AOFManager(self.filepath)

    def tearDown(self):
        self.aof.close()
        if os.path.exists(self.filepath):
            os.remove(self.filepath)

    def test_aof_write_and_load(self):
        self.aof.open()
        
        # Simulate write commands
        cmd1 = ["SET", "k1", "v1"]
        cmd2 = ["SET", "k2", "v2"]
        cmd3 = ["DEL", "k1"]
        
        self.aof.write(cmd1)
        self.aof.write(cmd2)
        self.aof.write(cmd3)
        self.aof.close()
        
        # Now make a new Database and CommandHandler
        new_db = Database(run_cleaner=False)
        new_handler = CommandHandler(new_db)
        
        # Load the AOF file
        load_count = self.aof.load(new_handler)
        self.assertEqual(load_count, 3)
        
        # Verify db state is restored
        self.assertIsNone(new_db.get("k1"))
        self.assertEqual(new_db.get("k2"), "v2")

if __name__ == "__main__":
    unittest.main()
