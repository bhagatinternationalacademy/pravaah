function createBackup(){

    alert(
        "Backup created successfully!"
    );
}

function scheduleBackup(){

    alert(
        "Automatic daily backup scheduled."
    );
}

function downloadBackup(){

    alert(
        "Downloading latest backup..."
    );
}

function restoreBackup(){

    const confirmRestore = confirm(
        "WARNING:\n\nThis will overwrite current ERP data.\n\nContinue?"
    );

    if(confirmRestore){

        alert(
            "System restored successfully."
        );
    }
}