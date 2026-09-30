import { PhoneIcon } from "lucide-react";
import { motion } from "framer-motion";
import { Button } from '@astryxdesign/core/Button';
import { Text } from '@astryxdesign/core/Text';

export default function CallToAction() {
    return (
        <motion.div className="flex flex-col max-w-5xl mt-40 px-4 mx-auto items-center justify-center text-center py-16 rounded-xl glass"
            initial={{ y: 150, opacity: 0 }}
            whileInView={{ y: 0, opacity: 1 }}
            viewport={{ once: true }}
            transition={{ type: "spring", stiffness: 320, damping: 70, mass: 1 }}
        >
            <motion.h2 className="text-2xl md:text-4xl font-medium mt-2"
                initial={{ y: 80, opacity: 0 }}
                whileInView={{ y: 0, opacity: 1 }}
                viewport={{ once: true }}
                transition={{ type: "spring", stiffness: 280, damping: 70, mass: 1 }}
            >
                Talk to Medline AI
            </motion.h2>
            <motion.p className="mt-4 text-sm/7 max-w-md"
                initial={{ y: 80, opacity: 0 }}
                whileInView={{ y: 0, opacity: 1 }}
                viewport={{ once: true }}
                transition={{ type: "spring", stiffness: 200, damping: 70, mass: 1 }}
            >
                Questions? Call now. Real help, fast.
            </motion.p>
            <motion.a
                href="tel:+256323200717"
                className="mt-6 text-4xl md:text-6xl font-bold tracking-tight text-[var(--genesis-accent)] hover:opacity-90 transition"
                initial={{ y: 80, opacity: 0 }}
                whileInView={{ y: 0, opacity: 1 }}
                viewport={{ once: true }}
                transition={{ type: "spring", stiffness: 280, damping: 70, mass: 1 }}
            >
                +256 323 200 717
            </motion.a>
            <motion.div className="mt-8"
                initial={{ y: 80, opacity: 0 }}
                whileInView={{ y: 0, opacity: 1 }}
                viewport={{ once: true }}
                transition={{ type: "spring", stiffness: 280, damping: 70, mass: 1 }}
            >
                <Button label="Call Medline AI" variant="primary" size="lg" icon={<PhoneIcon className="size-4" />} href="tel:+256323200717" as="a" style={{paddingInline: 'var(--spacing-8)', paddingBlock: 'var(--spacing-4)'}} />
            </motion.div>
        </motion.div>
    );
};