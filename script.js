const API_URL= "http://localhost:8000/reservas";

//crear la reserva
document.getElementById("reservationForm").addEventListener("submit", async function (e) {
    e.preventDefault();
    const data= {
        nombre: document.getElementById("nombre").value,
        telefono: document.getElementById("telefono").value,
        email: document.getElementById("email").value,
        fecha: document.getElementById("fecha").value,
        hora: document.getElementById("hora").value,
        personas: document.getElementById("personas").value,
        comentarios: document.getElementById("comentarios").value
    };

    const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    });
    const result = await res.json();
    mostrarMensaje(result.detail || "Reserva creada correctamente");
    document.getElementById("reservationForm").reset();
});






//reservass
window.buscarReservas = async function () {
    const email = document.getElementById("buscarEmail").value;
    if (!email) {
        mostrarMensaje("Por favor ingresa un email para buscar tus reservas.");
        return;
    }
    const res = await fetch(`${API_URL}?email=${encodeURIComponent(email)}`);
    const reservas = await res.json();
    mostrarReservas(reservas);
};



function mostrarReservas(reservas) {
    const lista = document.getElementById("listaReservas");
    lista.innerHTML = "";
    if (reservas.length === 0) {
        lista.innerHTML = "<p>No se encontraron reservas.</p>";
        return;
    }
    reservas.forEach(reserva => {
        const div = document.createElement("div");
        div.className = "reserva-item";
        div.innerHTML = `
            <strong>Nombre:</strong> <span>${reserva.nombre}</span><br>
            <strong>Fecha:</strong> <span>${reserva.fecha}</span> <strong>Hora:</strong> <span>${reserva.hora}</span><br>
            <strong>Personas:</strong> <span>${reserva.personas}</span><br>
            <strong>Comentarios:</strong> <span>${reserva.comentarios || "Ninguno"}</span><br>
            <button class="btn-edit" onclick="editarReserva(${reserva.id})">Editar</button>
            <button class="btn-delete" onclick="eliminarReserva(${reserva.id})">Eliminar</button>
        `;
        lista.appendChild(div);
    });
}




window.eliminarReserva = async function (id) {
    if (!confirm("Seguro que deseas eliminar esta reserva?")) return;
    const res = await fetch(`${API_URL}/${id}`, { method: "DELETE" });
    const result = await res.json();
    mostrarMensaje(result.detail || "Reserva eliminada");
    buscarReservas();
};




window.editarReserva = async function (id) {
    const res = await fetch(`${API_URL}/${id}`);
    const reserva = await res.json();
    document.getElementById("nombre").value = reserva.nombre;
    document.getElementById("telefono").value = reserva.telefono;
    document.getElementById("email").value = reserva.email;
    document.getElementById("fecha").value = reserva.fecha;
    document.getElementById("hora").value = reserva.hora;
    document.getElementById("personas").value = reserva.personas;
    document.getElementById("comentarios").value = reserva.comentarios;
    mostrarMensaje("Edita los datos y vuelve a enviar el formulario para actualizar la reserva.");

    

    document.getElementById("reservationForm").onsubmit = async function (e) {
        e.preventDefault();
        const data = {
            nombre: document.getElementById("nombre").value,
            telefono: document.getElementById("telefono").value,
            email: document.getElementById("email").value,
            fecha: document.getElementById("fecha").value,
            hora: document.getElementById("hora").value,
            personas: document.getElementById("personas").value,
            comentarios: document.getElementById("comentarios").value
        };
        const res = await fetch(`${API_URL}/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });
        const result = await res.json();
        mostrarMensaje(result.detail || "Reserva actualizada correctamente");
        document.getElementById("reservationForm").reset();
        buscarReservas();
        

        document.getElementById("reservationForm").onsubmit = null;
        document.getElementById("reservationForm").addEventListener("submit", async function (e) {
            e.preventDefault();
        }, { once: true });
    };
};






function mostrarMensaje(msg) {
    const mensaje = document.getElementById("mensaje");
    mensaje.textContent = msg;
    mensaje.style.display = "block";
    setTimeout(() => mensaje.style.display = "none", 3000);
}