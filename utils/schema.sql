CREATE TABLE IF NOT EXISTS buyers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    address TEXT NOT NULL,
    state TEXT NOT NULL,
    gst TEXT
);

CREATE TABLE IF NOT EXISTS challans(
    id SERIAL PRIMARY KEY,
    challan_number INT NOT NULL,
    session TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    buyer_id INT NOT NULL,
    cancelled BOOLEAN NOT NULL DEFAULT FALSE,

    -- Transportation details
    delivered_by TEXT NOT NULL,
    vehicle_number TEXT NOT NULL,
    received BOOLEAN NOT NULL DEFAULT FALSE,
    digitally_signed BOOLEAN NOT NULL DEFAULT FALSE,
    
    FOREIGN KEY (buyer_id) REFERENCES buyers (id)
);

CREATE TABLE IF NOT EXISTS products (
    challan_id SERIAL,
    name TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    description TEXT NOT NULL,
    serial_number TEXT NOT NULL,
    FOREIGN KEY (challan_id) REFERENCES challans (id),
    PRIMARY KEY(challan_id, serial_number)
);