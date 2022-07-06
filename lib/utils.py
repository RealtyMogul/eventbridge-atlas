def subnet_id_generator(subnets):
    """Creates a comma-separated stirng out of a list of VPC subnets.
    Intended for use in CfnOutput() functions.
    """
    subnet_list = []
    for subnet in subnets:
        subnet_list.append(str(subnet.subnet_id))
    print(subnet_list)
    subnet_list = ",".join(subnet_list)
    return subnet_list