/**
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
        console.log('\n📋 Current Todos:');
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
