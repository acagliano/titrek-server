
def init():
    pass

def main():
    if searchFor("humans"):
        if canCaptureTarget():
            if captureTarget():
                sayTaunt("mmmmm Yummy eyeball soup...")
        elif targetStrength()>10:
            runFromTarget()



