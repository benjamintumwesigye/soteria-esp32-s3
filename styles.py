main_styles = """
<style>
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    body {
        font-family: Arial, sans-serif;
        min-height: 100vh;
        display: flex;
        flex-direction: column;
        background-color: #f5f5f5;
    }

    header {
        background-color: #1c628e;
        color: white;
        padding: 1rem 1.5rem;
        position: sticky;
        top: 0;
        z-index: 1000;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    }

    .header-right {
        display: flex;
        gap: 1.5rem;
    }

    .header-left {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .header-right a {
        color: white;
        text-decoration: none;
        font-size: 1rem;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        transition: background-color 0.3s;
    }

    .header-right a:hover {
        background-color: rgba(255, 255, 255, 0.1);
        text-decoration: none;
    }

    .logo-icon {
        width: 50px; 
        height: 50px;
        border-radius: 50%;
    }
    
    .site-info {
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    .site-info h1 {
        font-size: 1.3rem;
        margin: 0;
        font-weight: 600;
    }

    .site-info p {
        font-size: 0.9rem; 
        margin: 0;
        line-height: 1.2;
        opacity: 0.9;
    }

    main {
        flex: 1;
        padding: 1.5rem;
        background-color: transparent;
    }

    .container {
        background-color: #fff;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        max-width: 600px;
        margin: 0 auto;
    }

    h2 {
        font-size: 1.5rem;
        margin-bottom: 1rem;
        color: #333;
    }

    h3 {
        font-size: 1.3rem;
        margin-bottom: 0.5rem;
        color: #333;
    }

    .status {
        background-color: #e7f3fe;
        border-left: 6px solid #2196F3;
        padding: 1rem;
        margin-bottom: 1.5rem;
        border-radius: 4px;
    }

    .status h4 {
        font-size: 1.2rem;
        margin-bottom: 0.5rem;
        color: #1c628e;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .status p {
        font-size: 0.95rem;
        margin: 0.3rem 0;
        color: #555;
    }

    .status-icon-connected {
        color: #28a745;
        font-size: 1.2rem;
    }

    .status-icon-disconnected {
        color: #dc3545;
        font-size: 1.2rem;
    }

    form label {
        font-size: 1rem;
        font-weight: 500;
        color: #333;
        margin-bottom: 0.3rem;
        display: block;
    }

    input[type=text], input[type=datetime-local], input[type=password], input[type=number] {
        width: 100%;
        padding: 12px 15px;
        margin: 0.5rem 0 1rem 0;
        display: inline-block;
        border: 1px solid #ccc;
        border-radius: 4px;
        box-sizing: border-box;
        font-size: 1rem;
        transition: border-color 0.3s, box-shadow 0.3s;
    }

    input[type=text]:focus, input[type=datetime-local]:focus, input[type=password]:focus, input[type=number]:focus {
        border-color: #1c628e;
        box-shadow: 0 0 5px rgba(28, 98, 142, 0.3);
        outline: none;
    }

    select {
        width: 100%;
        padding: 12px 15px;
        margin: 0.5rem 0 1rem 0;
        display: inline-block;
        border: 1px solid #ccc;
        border-radius: 4px;
        box-sizing: border-box;
        font-size: 1rem;
        background-color: white;
        -webkit-appearance: none;
        -moz-appearance: none;
        appearance: none;
        background-image: url('data:image/svg+xml;utf8,<svg fill="gray" height="24" viewBox="0 0 24 24" width="24" xmlns="http://www.w3.org/2000/svg"><path d="M7 10l5 5 5-5z"/></svg>');
        background-repeat: no-repeat;
        background-position: right 10px center;
        transition: border-color 0.3s, box-shadow 0.3s;
    }

    select:focus {
        border-color: #1c628e;
        box-shadow: 0 0 5px rgba(28, 98, 142, 0.3);
        outline: none;
    }

    /* Checkbox styling */
    .checkbox-group {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin: 0.5rem 0;
    }

    input[type=checkbox] {
        width: 18px;
        height: 18px;
        margin: 0;
        cursor: pointer;
        accent-color: #1c628e; /* Modern browsers support this for custom checkbox color */
    }

    .checkbox-group label {
        font-size: 1rem;
        font-weight: 400;
        color: #333;
        margin: 0;
        cursor: pointer;
        display: inline; /* Ensure label stays inline with checkbox */
    }

    .checkbox-group:hover label {
        color: #1c628e; /* Subtle hover effect */
    }

    input[type=submit] {
        width: 100%;
        background-color: #1c628e;
        color: white;
        padding: 14px 20px;
        margin: 1rem 0 0 0;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 1rem;
        font-weight: 500;
        transition: background-color 0.3s;
    }

    input[type=submit]:hover {
        background-color: #155a7f;
    }

    .table-container {
        width: 100%;
        overflow-x: auto;
        margin-bottom: 20px;
    }

    table {
        width: 100%;
        min-width: 600px;
        border-collapse: collapse;
        margin-bottom: 0;
    }

    th, td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
        white-space: nowrap;
    }

    th {
        background-color: #f2f2f2;
    }

    tr:nth-child(even) {
        background-color: #f9f9f9;
    }

    tr:hover {
        background-color: #ddd;
    }

    footer {
        background-color: #1c628e;
        color: white;
        padding: 1rem;
        text-align: center;
        position: sticky;
        bottom: 0;
        font-size: 0.9rem;
    }

    body, main {
        overflow-x: hidden;
    }

    /* Mobile-specific adjustments */
    @media (max-width: 768px) {
        header {
            padding: 0.8rem 1rem;
            font-size: 1.2rem;
        }

        .header-right {
            gap: 1rem;
        }

        .header-right a {
            padding: 0.4rem 0.8rem;
        }

        .site-info h1 {
            font-size: 1.2rem;
        }

        .site-info p {
            font-size: 0.85rem;
        }

        main {
            padding: 1rem;
        }

        .container {
            padding: 1rem;
        }

        h2 {
            font-size: 1.3rem;
        }

        h3 {
            font-size: 1.1rem;
        }

        .status h4 {
            font-size: 1.1rem;
        }

        .status p {
            font-size: 0.9rem;
        }

        select, input[type=text], input[type=password], input[type=number] {
            font-size: 0.9rem;
            padding: 10px 12px;
        }

        input[type=submit] {
            padding: 12px 15px;
            font-size: 0.95rem;
        }

        .checkbox-group {
            gap: 0.4rem;
        }

        input[type=checkbox] {
            width: 16px;
            height: 16px;
        }

        .checkbox-group label {
            font-size: 0.9rem;
        }

        footer {
            padding: 0.8rem;
            font-size: 0.85rem;
        }

        .table-container {
            -webkit-overflow-scrolling: touch;
        }
    }
</style>
"""


# Define CSS styles for the table
table_style = """
<style>
    .table-container {
        width: 100%;              
        overflow-x: auto;        
        margin-bottom: 20px;     
    }

    /* Table styles */
    table {
        width: 100%;             
        min-width: 600px;        
        border-collapse: collapse;
        margin-bottom: 0;         
    }

    th, td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
        white-space: nowrap;     
    }

    th {
        background-color: #f2f2f2;
    }

    tr:nth-child(even) {
        background-color: #f9f9f9;
    }

    tr:hover {
        background-color: #ddd;
    }
</style>
"""
