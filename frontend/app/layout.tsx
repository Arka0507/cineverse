import type {Metadata} from 'next';
import './globals.css';
export const metadata:Metadata={title:'Cineverse — A world of great cinema',description:'Discover your next favorite movie with personalized recommendations and a new way to explore.'};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body>{children}</body></html>;}
