-- Create the Library table
CREATE TABLE Library (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255) NOT NULL
);

-- Create the AccessPoint table
CREATE TABLE AccessPoint (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    library_id INT NOT NULL,
    FOREIGN KEY (library_id) REFERENCES Library(id) ON DELETE CASCADE
);

-- Create the Utilization table
CREATE TABLE Utilization (
    id SERIAL PRIMARY KEY,
    accesspoint_id INT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    user_count INT CHECK (user_count >= 0),
    FOREIGN KEY (accesspoint_id) REFERENCES AccessPoint(id) ON DELETE CASCADE
);
