
def subintf_cleanup_gen_main():
    for subintf_num in range(115,3000):
        print("no interface po10.%s" % subintf_num)

if __name__=='__main__':
    subintf_cleanup_gen_main()
