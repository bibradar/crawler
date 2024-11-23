DROP TABLE Library CASCADE;
-- Create the Library table
CREATE TABLE Library (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    bib VARCHAR(255) NOT NULL,
    uni VARCHAR(255) NOT NULL,
    location VARCHAR(255) NOT NULL
);

INSERT INTO Library (name, bib, uni, location) VALUES ('Fachbibliothek Philologicum', 'Fachbibliothek Philologicum', 'LMU', 'Ludwigstr. 25\n 80539 München');

-- Create the AccessPoint table
CREATE TABLE AccessPoint (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    library_id INT NOT NULL,
    FOREIGN KEY (library_id) REFERENCES Library(id) ON DELETE CASCADE
);

-- Create the Utilization table
CREATE TABLE Utilization (
    accesspoint_id INT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    user_count INT CHECK (user_count >= 0),
    FOREIGN KEY (accesspoint_id) REFERENCES AccessPoint(id) ON DELETE CASCADE,
    PRIMARY KEY (accesspoint_id, timestamp)
);
