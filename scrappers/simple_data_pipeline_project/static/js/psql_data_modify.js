document.addEventListener("DOMContentLoaded", () => {
    const deleteButtons = document.querySelectorAll(".delete-btn");

    deleteButtons.forEach(button => {
        button.addEventListener("click", (event) => {
            const tableName = event.target.dataset.table;
            const confirmed = confirm(`Are you sure you want to delete the table: ${tableName}?`);
            if (!confirmed) {
                event.preventDefault();
            }
        });
    });
});
