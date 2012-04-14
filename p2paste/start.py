# -*- coding: utf-8 -*-
import site
import os


def starter():
    current_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    site.sys.path.append(current_dir)
    
    from p2paste.main import main
    main()

if __name__ == '__main__':
    starter()
    
    