
def subintf_cleanup_gen_main():
    for subintf_num in range(104,3000):
        print("no interface po20.%s" % subintf_num)

if __name__=='__main__':
    subintf_cleanup_gen_main()
