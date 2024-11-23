-- Create the Library table
CREATE TABLE Library (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255) NOT NULL
);

INSERT INTO Library (name, location) VALUES ('LMU, Fachbibliothek Philologicum', 'Ludwigstr. 25\n 80539 München');

DROP TABLE AccessPoint CASCADE;
-- Create the AccessPoint table
CREATE TABLE AccessPoint (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    library_id INT NOT NULL,
    FOREIGN KEY (library_id) REFERENCES Library(id) ON DELETE CASCADE
);

DROP TABLE Utilization;
-- Create the Utilization table
CREATE TABLE Utilization (
    accesspoint_id INT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    user_count INT CHECK (user_count >= 0),
    FOREIGN KEY (accesspoint_id) REFERENCES AccessPoint(id) ON DELETE CASCADE,
    PRIMARY KEY (accesspoint_id, timestamp)
);
