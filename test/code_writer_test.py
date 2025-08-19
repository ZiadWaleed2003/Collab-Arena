#!/usr/bin/env python3
"""
Test script for CodeWriterTool
Tests the tool with fake code data and saves to results/tool_tests directory
"""

import sys
import os
from datetime import datetime

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.EnviromentModule.tools.code_writer_tool import execute
from src.EnviromentModule.workspace_manager import WorkspaceManager

def test_code_writer_tool():
    """Test the CodeWriterTool with various fake code samples"""
    
    print("🧪 Testing CodeWriterTool...")
    print("=" * 50)
    
    # # Initialize the tool
    # code_writer = CodeWriterTool()
    
    # Test cases with fake code
    test_cases = [
        {
            "name": "Python Calculator",
            "file_path": "results/tool_tests/calculator.py",
            "content": '''#!/usr/bin/env python3
"""
Simple Calculator Module
Generated for testing CodeWriterTool
"""

class Calculator:
    """A simple calculator class for basic arithmetic operations"""
    
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        """Add two numbers"""
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def subtract(self, a, b):
        """Subtract b from a"""
        result = a - b
        self.history.append(f"{a} - {b} = {result}")
        return result
    
    def multiply(self, a, b):
        """Multiply two numbers"""
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result
    
    def divide(self, a, b):
        """Divide a by b"""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        result = a / b
        self.history.append(f"{a} / {b} = {result}")
        return result
    
    def get_history(self):
        """Get calculation history"""
        return self.history

if __name__ == "__main__":
    calc = Calculator()
    print("Calculator Test:")
    print(f"5 + 3 = {calc.add(5, 3)}")
    print(f"10 - 4 = {calc.subtract(10, 4)}")
    print(f"6 * 7 = {calc.multiply(6, 7)}")
    print(f"15 / 3 = {calc.divide(15, 3)}")
    print("\\nHistory:")
    for entry in calc.get_history():
        print(f"  {entry}")
''',
            "mode": "w"
        },
        {
            "name": "JavaScript To-Do App",
            "file_path": "results/tool_tests/todo_app.js",
            "content": '''/**
 * Simple To-Do List Application
 * Generated for testing CodeWriterTool
 */

class TodoApp {
    constructor() {
        this.todos = [];
        this.nextId = 1;
    }

    /**
     * Add a new todo item
     * @param {string} text - The todo text
     * @param {string} priority - Priority level (high, medium, low)
     */
    addTodo(text, priority = 'medium') {
        const todo = {
            id: this.nextId++,
            text: text,
            priority: priority,
            completed: false,
            createdAt: new Date().toISOString()
        };
        
        this.todos.push(todo);
        console.log(`✅ Added todo: "${text}" with priority: ${priority}`);
        return todo;
    }

    /**
     * Mark a todo as completed
     * @param {number} id - Todo ID
     */
    completeTodo(id) {
        const todo = this.todos.find(t => t.id === id);
        if (todo) {
            todo.completed = true;
            console.log(`✔️ Completed todo: "${todo.text}"`);
        } else {
            console.log(`❌ Todo with ID ${id} not found`);
        }
    }

    /**
     * Get all todos filtered by status
     * @param {string} filter - 'all', 'active', 'completed'
     */
    getTodos(filter = 'all') {
        switch (filter) {
            case 'active':
                return this.todos.filter(t => !t.completed);
            case 'completed':
                return this.todos.filter(t => t.completed);
            default:
                return this.todos;
        }
    }

    /**
     * Display todos in a formatted way
     */
    displayTodos() {
        console.log('\\n📋 Current Todos:');
        console.log('=================');
        
        if (this.todos.length === 0) {
            console.log('No todos yet. Add some tasks!');
            return;
        }

        this.todos.forEach(todo => {
            const status = todo.completed ? '✅' : '⏳';
            const priority = todo.priority.toUpperCase();
            console.log(`${status} [${priority}] ${todo.text}`);
        });
    }
}

// Example usage
const app = new TodoApp();
app.addTodo('Learn JavaScript', 'high');
app.addTodo('Build a web app', 'medium');
app.addTodo('Write tests', 'high');
app.addTodo('Deploy to production', 'low');

app.displayTodos();
app.completeTodo(1);
app.displayTodos();
''',
            "mode": "w"
        },
        {
            "name": "Configuration File",
            "file_path": "results/tool_tests/config.json",
            "content": '''{
    "app_name": "Collab-Arena Test Application",
    "version": "1.0.0",
    "environment": "development",
    "database": {
        "host": "localhost",
        "port": 5432,
        "name": "collab_arena_test",
        "ssl": false
    },
    "api": {
        "base_url": "http://localhost:8000",
        "timeout": 30000,
        "rate_limit": {
            "requests_per_minute": 100,
            "burst_size": 10
        }
    },
    "features": {
        "enable_logging": true,
        "debug_mode": true,
        "cache_enabled": false,
        "experimental_features": [
            "new_ui",
            "advanced_search",
            "real_time_collaboration"
        ]
    },
    "security": {
        "jwt_secret": "your-secret-key-here",
        "session_timeout": 3600,
        "password_requirements": {
            "min_length": 8,
            "require_special_chars": true,
            "require_numbers": true
        }
    },
    "generated_at": "2025-08-19T10:30:00Z",
    "test_data": true
}''',
            "mode": "w"
        }
    ]
    
    # Run tests
    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"\\n🔍 Test {i}: {test_case['name']}")
        print("-" * 30)
        
        # Prepare params (no need for state since it's not used)
        params = {
            "file_path": test_case["file_path"],
            "content": test_case["content"],
            "mode": test_case["mode"]
        }
        
        # Execute the tool - use invoke method for LangChain tools
        result = execute.invoke({"tool_input": params})
        results.append(result)
        
        # Display results
        if result["success"]:
            print(f"✅ SUCCESS: {result['message']}")
            print(f"📁 File: {result['file_path']}")
            print(f"📊 Bytes written: {result['bytes_written']}")
            if result.get('file_info'):
                print(f"📋 File info: Size={result['file_info'].get('size_bytes', 'N/A')} bytes")
        else:
            print(f"❌ FAILED: {result['message']}")
    
    # Summary
    print("\\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    successful = sum(1 for r in results if r["success"])
    total = len(results)
    
    print(f"✅ Successful: {successful}/{total}")
    print(f"❌ Failed: {total - successful}/{total}")
    
    if successful == total:
        print("\\n🎉 All tests passed! CodeWriterTool is working correctly.")
    else:
        print("\\n⚠️  Some tests failed. Check the error messages above.")
    
    return results

if __name__ == "__main__":
    test_results = test_code_writer_tool()
