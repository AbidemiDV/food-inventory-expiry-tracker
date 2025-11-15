document.addEventListener('DOMContentLoaded', () => {
    const addForm = document.getElementById('addForm');
    const itemsTableBody = document.querySelector('#itemsTable tbody');
    const recipesList = document.getElementById('recipesList');
    const exportBtn = document.getElementById('exportBtn');

    async function fetchItems() {
        const res = await fetch('/api/items');
        const data = await res.json();
        itemsTableBody.innerHTML = '';
        data.items.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><input type="checkbox" class="select-item" data-id="${item.id}"></td>
                <td>${item.name}</td>
                <td>${item.category}</td>
                <td>${item.qty}</td>
                <td>${item.expiry || ''}</td>
                <td>${item.days_left !== null ? item.days_left : ''}</td>
                <td>${item.notes}</td>
                <td>
                    <button class="delete-btn" data-id="${item.id}">Delete</button>
                </td>
            `;
            itemsTableBody.appendChild(row);
        });
        fetchRecipes();
    }

    async function fetchRecipes() {
        const res = await fetch('/api/recipes');
        const data = await res.json();
        recipesList.innerHTML = '';
        data.recipes.forEach(r => {
            const li = document.createElement('li');
            li.textContent = r;
            recipesList.appendChild(li);
        });
    }

    addForm.addEventListener('submit', async(e) => {
        e.preventDefault();
        const formData = new FormData(addForm);
        const payload = {};
        formData.forEach((v, k) => payload[k] = v);
        await fetch('/api/items', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        addForm.reset();
        fetchItems();
    });

    itemsTableBody.addEventListener('click', async(e) => {
        if (e.target.classList.contains('delete-btn')) {
            const id = e.target.dataset.id;
            await fetch(`/api/items/${id}`, { method: 'DELETE' });
            fetchItems();
        }
    });

    exportBtn.addEventListener('click', async() => {
        const selected = [...document.querySelectorAll('.select-item:checked')].map(i => i.dataset.id);
        const allRes = await fetch('/api/items');
        const data = await allRes.json();
        const itemsToExport = data.items.filter(i => selected.includes(i.id.toString()));
        const res = await fetch('/api/export_shopping', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ items: itemsToExport })
        });
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'shopping_list.csv';
        document.body.appendChild(a);
        a.click();
        a.remove();
    });

    fetchItems();
});