
const screen = document.getElementById("screen");
const resultBox = document.getElementById("result");
const expressionInput = document.getElementById("expression");
const statusBox = document.getElementById("status");

// Convert bottom-left-origin coordinates into CSS grid positions.
// CSS grid starts at the top-left, so row 0 is displayed as row 9.
document.querySelectorAll(".keypad [data-col][data-row]").forEach(button => {
    const column = Number(button.dataset.col);
    const row = Number(button.dataset.row);

    button.style.gridColumn = String(column + 1);
    button.style.gridRow = String(9 - row);
});

function updateScreen() {
    screen.textContent = expressionInput.value || "0";
}

function insertText(value) {
    const start = expressionInput.selectionStart;
    const end = expressionInput.selectionEnd;
    const current = expressionInput.value;

    expressionInput.value =
        current.slice(0, start) + value + current.slice(end);

    const cursor = start + value.length;

    expressionInput.focus();
    expressionInput.setSelectionRange(cursor, cursor);

    updateScreen();
}

function clearInput() {
    expressionInput.value = "";
    screen.textContent = "0";
    resultBox.textContent = "";
    statusBox.textContent = "Ready · Angles in radians";

    expressionInput.focus();
}

function deleteLast() {
    const start = expressionInput.selectionStart;
    const end = expressionInput.selectionEnd;
    const current = expressionInput.value;

    if (start !== end) {
        expressionInput.value =
            current.slice(0, start) + current.slice(end);

        expressionInput.setSelectionRange(start, start);
    } else if (start > 0) {
        expressionInput.value =
            current.slice(0, start - 1) + current.slice(end);

        expressionInput.setSelectionRange(start - 1, start - 1);
    }

    updateScreen();
    expressionInput.focus();
}

async function calculate(operation = "evaluate") {
    const expression = expressionInput.value.trim();

    if (!expression) {
        statusBox.textContent = "Enter an expression first.";
        return;
    }

    const payload = {
        expression,
        operation,
        variable: document.getElementById("variable").value
    };

    if (operation === "definite_integrate") {
        payload.lower = document.getElementById("lower").value;
        payload.upper = document.getElementById("upper").value;
    }

    statusBox.textContent = "Calculating…";

    try {
        const response = await fetch("/api/calculate", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.error || "Calculation failed.");
        }

        resultBox.textContent =
            `${data.result.exact}\n≈ ${data.result.decimal}`;

        screen.textContent = data.result.exact;
        statusBox.textContent = "Calculation complete";
    } catch (error) {
        resultBox.textContent = error.message;
        statusBox.textContent = "Check your expression";
    }
}

document.querySelectorAll("[data-insert]").forEach(button => {
    button.addEventListener("click", () => {
        const value = button.dataset.insert;

        // Functions get parentheses with the cursor inside.
        const functions = [
            "sin(", "cos(", "tan(",
            "arcsin(", "arccos(", "arctan(",
            "log(", "ln(", "sqrt(",
            "exp(", "sinh(", "cosh(", "tanh(",
            "factorial("
        ];

        if (functions.includes(value)) {
            const start = expressionInput.selectionStart;
            const end = expressionInput.selectionEnd;
            const current = expressionInput.value;
            const inserted = value + ")";

            expressionInput.value =
                current.slice(0, start) +
                inserted +
                current.slice(end);

            const cursor = start + value.length;

            expressionInput.focus();
            expressionInput.setSelectionRange(cursor, cursor);
            updateScreen();
        } else {
            // The √ button inserts the symbol directly.
            // This permits input such as 3√8 and √4.
            insertText(value);
        }
    });
});

document.getElementById("clear").addEventListener("click", clearInput);
document.getElementById("delete").addEventListener("click", deleteLast);

document.getElementById("equals").addEventListener("click", () => {
    calculate("evaluate");
});

document.getElementById("differentiate").addEventListener("click", () => {
    calculate("differentiate");
});

document.getElementById("integrate").addEventListener("click", () => {
    calculate("integrate");
});

document.getElementById("definite-integrate").addEventListener("click", () => {
    calculate("definite_integrate");
});

expressionInput.addEventListener("input", () => {
    updateScreen();
});

expressionInput.addEventListener("keydown", event => {
    if (event.key === "Enter") {
        event.preventDefault();
        calculate("evaluate");
    }
});
