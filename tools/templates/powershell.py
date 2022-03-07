import os

def build_template(path: str, root_directory: str):

    with open(os.path.join(path, root_directory, "collector.ps1"),'w') as collector:
        collector.write(
"""
if ($args.count -eq 0){
	Write-host "No arguments"
}elseif ($args[0] -eq "collect"){
	Write-host "Powershell collect"
}elseif ($args[0] -eq "test"){
	Write-host "Powershell test"
}else{
	Write-host "Command not found"
}

"""
        )
