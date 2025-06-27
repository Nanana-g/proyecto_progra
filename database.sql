CREATE DATABASE IF NOT EXISTS `sip&joy` 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE `sip&joy`;

CREATE TABLE IF NOT EXISTS reservas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    telefono VARCHAR(20) NOT NULL,
    email VARCHAR(100) NOT NULL,
    fecha DATE NOT NULL,
    hora TIME NOT NULL,
    personas INT NOT NULL,
    comentarios TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_fecha (fecha)
);

INSERT INTO reservas (nombre, telefono, email, fecha, hora, personas, comentarios) VALUES
('María González', '8888-1234', 'maria@email.com', '2025-06-27', '10:00:00', 2, 'Mesa cerca de la ventana'),
('Carlos Rodríguez', '8888-5678', 'carlos@email.com', '2025-06-27', '14:00:00', 4, 'Cumpleaños'),
('Ana López', '8888-9999', 'ana@email.com', '2025-06-28', '09:00:00', 1, 'Sin gluten'),
('Pedro Jiménez', '8888-7777', 'pedro@email.com', '2025-06-28', '16:00:00', 3, 'Primera cita');

SELECT * FROM reservas;

SELECT COUNT(*) as total_reservas FROM reservas;

SELECT fecha, COUNT(*) as cantidad_reservas 
FROM reservas 
GROUP BY fecha 
ORDER BY fecha;

SELECT fecha, SUM(personas) as total_personas 
FROM reservas 
GROUP BY fecha 
ORDER BY fecha;

SELECT * FROM reservas WHERE email LIKE '%maria%';

SELECT * FROM reservas WHERE fecha = CURDATE();

SELECT * FROM reservas WHERE fecha > CURDATE();

SELECT hora, COUNT(*) as frecuencia 
FROM reservas 
GROUP BY hora 
ORDER BY frecuencia DESC;