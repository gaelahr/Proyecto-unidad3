
CREATE DATABASE IF NOT EXISTS uni3;


USE uni3;

CREATE TABLE IF NOT EXISTS P9_roles (
    role_id INT PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS P9_users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role_id INT NOT NULL DEFAULT 2,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES P9_roles(role_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS P9_attendance (
    attendance_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    address VARCHAR(255),
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES P9_users(user_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS p10_foto (
    id INT PRIMARY KEY AUTO_INCREMENT,
    descripcion VARCHAR(255) NOT NULL,
    ruta_foto VARCHAR(255) NOT NULL,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;


CREATE TABLE IF NOT EXISTS P9_packages (
    package_id INT PRIMARY KEY AUTO_INCREMENT,
    address VARCHAR(255) NOT NULL,
    description VARCHAR(255),
    assigned_to_user_id INT,
    is_delivered BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (assigned_to_user_id) REFERENCES P9_users(user_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS P9_deliveries (
    delivery_id INT PRIMARY KEY AUTO_INCREMENT,
    package_id INT UNIQUE, -- UNIQUE para asegurar que un paquete solo se entregue una vez
    delivered_by_user_id INT,
    delivery_latitude DECIMAL(10, 8) NOT NULL,
    delivery_longitude DECIMAL(11, 8) NOT NULL,
    delivery_address VARCHAR(255),
    photo_route VARCHAR(255),
    delivered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (package_id) REFERENCES P9_packages(package_id),
    FOREIGN KEY (delivered_by_user_id) REFERENCES P9_users(user_id)
) ENGINE=InnoDB;

-- Paquete 4: Un pedido urgente asignado al Agente 3
INSERT INTO P9_packages (address, description, assigned_to_user_id, is_delivered) 
VALUES 
('Calle de los Pinos 555, Res. El Bosque', 'Documentos legales urgentes (Sobre grande)', 3, 0);

-- Paquete 5: Un artículo electrónico
INSERT INTO P9_packages (address, description, assigned_to_user_id, is_delivered) 
VALUES 
('Av. Central, Plaza Comercial Local 15', 'Consola de videojuegos (Caja mediana)', 3, 0);

-- Paquete 6: Un artículo voluminoso
INSERT INTO P9_packages (address, description, assigned_to_user_id, is_delivered) 
VALUES 
('Fraccionamiento Las Lomas, Lote 12', 'Mueble desarmado (Requiere dos personas)', 3, 0);

-- Paquete 7: Un pedido pequeño en otra ciudad
INSERT INTO P9_packages (address, description, assigned_to_user_id, is_delivered) 
VALUES 
('Carretera Federal Km 40, Ciudad Beta', 'Kit de herramientas pequeñas', 3, 0);