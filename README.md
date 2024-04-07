# Terraform Crawl Scrape Parser

Todo
- [ ] Fetch all referenced "source" local data given terraform project
- [ ] Fetch all declared imported external data 
- [ ] Identify relevant resources
- [ ] ... 


Get all project from github that
- have more than 5 stars
- contain a main.tf file



## Focus Resources
"aws_lambda_function", # https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function
"aws_eks_cluster",  # https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/eks_cluster
"aws_instance",  # https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/instance

"google_cloudfunctions_function", # https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloudfunctions_function
"google_vmwareengine_cluster", # https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/vmwareengine_cluster
"google_compute_instance", # https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_instancey

"azurerm_linux_function_app", # https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/linux_function_app
"azurerm_windows_function_app", # https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/windows_function_app
"azurerm_kubernetes_cluster", # https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/kubernetes_cluster
"azurerm_virtual_machine", # https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/virtual_machine


# python notebook para investigação
# medir labels dentro de cada serviço/ contagem